from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from itertools import count
import sys
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading
import json

from arguments import parse_arguments
from payload_manager import PayloadManager
from request_manager import make_attempt, check_success
from authenticator import Authenticator


def main():
    """Main function to run the brute-force tool."""
    args = parse_arguments()
    brute_forcer = BruteForcer(args)
    brute_forcer.run()


class BruteForcer:
    """Handles the brute-force attack orchestration."""

    def __init__(self, args):
        self.args = args
        self.stop_event = threading.Event()
        self.successes = []
        self.attempt_counter = count(1)
        self.failed_attempts = 0
        self.output_file = None
        self.auth = None
        self.sessions = self._setup_sessions()
        self.requeue_counts = Counter()
        self.constants = {}
        self.payload_manager = None

    def run(self):
        """Executes the brute-force attack."""
        if self.args.output:
            try:
                self.output_file = open(self.args.output, "a", encoding="utf-8")
            except IOError as e:
                print(f"[-] Error opening output file: {e}", file=sys.stderr)
                sys.exit(1)

        param_vars = {
            'param': self.args.param,
            'cookie': self.args.cookie,
        }
        # Build payload manager (it streams combinations and shares constants/increment fields)
        self.payload_manager = PayloadManager(
            param_vars=param_vars,
            zip_fields=self.args.zip_fields,
            product_fields=self.args.product_fields,
            attempt_counter=self.attempt_counter,
        )
        self.constants = self.payload_manager.constants
        # Expose increment fields for request execution
        self.args.increment_fields = self.payload_manager.increment_fields

        if self.args.reauth > 0:
            self._setup_authentication()

        combos_iter = self.payload_manager.generate_combinations()

        self._print_attack_info()

        try:
            with ThreadPoolExecutor(max_workers=self.args.threads) as executor:
                self._process_tasks(executor, combos_iter)
        except KeyboardInterrupt:
            print("\n(+) Keyboard interrupt received. Shutting down gracefully...")
            self.stop_event.set()
        finally:
            self._cleanup()
            self._print_results()

    def _setup_sessions(self):
        """Creates a pool of requests sessions."""
        retry_cfg = Retry(
            total=self.args.retries,
            backoff_factor=self.args.retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_cfg, pool_connections=self.args.threads, pool_maxsize=self.args.threads * 2)
        
        sessions = [requests.Session() for _ in range(self.args.threads)]
        for session in sessions:
            session.mount("http://", adapter)
            session.mount("https://", adapter)
        return sessions

    def _setup_authentication(self):
        """Initializes the authenticator and performs initial authentication.
        Updates constants and applies the cookie to all sessions.
        """
        if not all([self.args.login_url, self.args.username, self.args.password]):
            print("[-] Error: --reauth requires --login-url, --username, and --password.", file=sys.stderr)
            sys.exit(1)

        auth_headers = dict(h.split(":", 1) for h in self.args.auth_header or [])
        self.auth = Authenticator(self.args.login_url, self.args.username, self.args.password,
                                  self.args.proxy_url, self.args.insecure, auth_headers, self.args.auth_cookie_name)
        try:
            print("(+) Performing initial authentication...")
            session_cookie = self.auth.authenticate()
            # Update constants used for future payload generation
            self.constants[f"cookie:{self.args.auth_cookie_name}"] = session_cookie
            # Apply cookie to all existing sessions immediately
            cookie_name = self.args.auth_cookie_name
            for session in self.sessions:
                session.cookies.set(cookie_name, session_cookie)
            print(f"(+) Initial authentication successful. Session cookie set.")
        except Exception as e:
            print(f"[-] Initial authentication failed: {e}", file=sys.stderr)
            sys.exit(1)

    def _process_tasks(self, executor, combos_iter):
        """Manages the submission and processing of tasks to the thread pool."""
        futures = set()
        # Track futures so re-queues are also monitored
        tracked_futures = futures
        attempts_made = 0
        
        # Initial pool of tasks
        for i in range(self.args.threads):
            try:
                payload, attempt_num = next(combos_iter)
                session = self.sessions[i % self.args.threads]
                fut = executor.submit(self._task_wrapper, payload, attempt_num, session)
                futures.add(fut)
                attempts_made += 1
                if self.args.max_attempts and attempts_made >= self.args.max_attempts:
                    break
            except StopIteration:
                break

        while futures:
            for future in as_completed(list(futures)):
                futures.remove(future)
                
                if self.stop_event.is_set():
                    continue

                result = future.result()
                
                # Check if the result was an error that needs re-queuing
                payload, attempt_num, response, elapsed, *error = result
                if error:
                    new_future = self._handle_error(executor, result)
                    if new_future is not None:
                        futures.add(new_future)
                else:
                    self._handle_result(result)

                # Schedule a new task if the attack is not stopping
                if not self.stop_event.is_set():
                    try:
                        if not self.args.max_attempts or attempts_made < self.args.max_attempts:
                            next_payload, next_attempt_num = next(combos_iter)
                            session = self.sessions[next_attempt_num % self.args.threads]
                            fut = executor.submit(self._task_wrapper, next_payload, next_attempt_num, session)
                            futures.add(fut)
                            attempts_made += 1
                    except StopIteration:
                        # No more new payloads to schedule
                        pass

    def _task_wrapper(self, payload, attempt_num, session):
        """Wrapper for each task to handle exceptions and verbosity."""
        if self.stop_event.is_set():
            return None, None, None, None
        
        if self.args.verbose:
            print(f"(+) Attempt {attempt_num}: {payload}")

        return make_attempt(self.args.url, payload, attempt_num, self.args, session)

    def _handle_result(self, result):
        """Processes the result of a single attempt."""
        payload, _, response, elapsed, *error = result
        
        if response and check_success(response, elapsed, self.args):
            self._handle_success(payload, response, elapsed)
        elif response:
            self.failed_attempts += 1
            if self.args.verbose:
                print(f"[-] Failed: {payload} (Status: {response.status_code}, Time: {elapsed:.2f}s, Length: {len(response.text)})")
            self._check_reauth()

    def _handle_error(self, executor, result):
        """Handles a request error, including re-queuing."""
        payload, attempt_num, _, _, error_msg = result
        payload_key = tuple(sorted(payload.items()))
        
        print(f"[-] Request Error: {payload} - {error_msg}", file=sys.stderr)
        self.failed_attempts += 1

        self.requeue_counts[payload_key] += 1
        max_retries = self.args.per_payload_max_retries
        
        if max_retries == 0 or self.requeue_counts[payload_key] <= max_retries:
            print(f"    -> Re-submitting payload (retry {self.requeue_counts[payload_key]}/{max_retries or 'inf'}).")
            session = self.sessions[attempt_num % self.args.threads]
            # Re-submit the task to the executor
            fut = executor.submit(self._task_wrapper, payload, attempt_num, session)
            return fut
        else:
            print(f"    -> Max retries reached for payload. It will not be tried again.", file=sys.stderr)
            fut = None

        self._check_reauth()
        return None

    def _handle_success(self, payload, response, elapsed):
        """Handles a successful attempt."""
        self.successes.append(payload)
        self.failed_attempts = 0
        print(f"[+] SUCCESS: {payload}")
        print(f"    Status: {response.status_code}, Time: {elapsed:.2f}s, Length: {len(response.text)}")

        if self.output_file:
            json.dump({"payload": payload, "status": response.status_code, "time": elapsed, "length": len(response.text)}, self.output_file)
            self.output_file.write('\n')
            self.output_file.flush()

        if self.args.stop_on_success:
            self.stop_event.set()

    def _check_reauth(self):
        """Checks if re-authentication is needed and performs it."""
        if self.auth and self.failed_attempts >= self.args.reauth > 0:
            print("(+) Re-authenticating...")
            try:
                session_cookie = self.auth.authenticate()
                # Update cookie on all sessions for subsequent requests
                cookie_name = self.args.auth_cookie_name
                for session in self.sessions:
                    session.cookies.set(cookie_name, session_cookie)
                # Update constants so future generated payloads include the fresh cookie
                self.constants[f"cookie:{cookie_name}"] = session_cookie
                print("(+) Re-authentication successful; refreshed session cookie applied.")
                self.failed_attempts = 0
            except Exception as e:
                print(f"[-] Re-authentication failed: {e}. Exiting.", file=sys.stderr)
                self.stop_event.set()

    def _print_attack_info(self):
        """Prints information about the upcoming attack."""
        print(f"(+) Starting brute-force on {self.args.url} with method {self.args.method}")
        pm = self.payload_manager
        if pm.brute_fields:
            print(f"(+) Brute-force fields: {[key for key, _ in pm.brute_fields]}")
        if pm.zip_fields:
            print(f"(+) Zipped fields: {pm.zip_fields}")
        if pm.product_fields:
            print(f"(+) Product fields: {pm.product_fields}")
        if pm.increment_fields:
            print(f"(+) Incrementing fields: {pm.increment_fields}")
        if pm.constants:
            print(f"(+) Constant fields: {pm.constants}")

    def _cleanup(self):
        """Cleans up resources like sessions and files."""
        for session in self.sessions:
            session.close()
        if self.auth:
            self.auth.close()
        if self.output_file:
            self.output_file.close()

    def _print_results(self):
        """Prints the final results of the attack."""
        if not self.successes:
            print("(-) No successful combinations found.")
        else:
            print("\n(+) Successful combinations found:")
            for combo in self.successes:
                print(f"    {combo}")


if __name__ == "__main__":
    main()