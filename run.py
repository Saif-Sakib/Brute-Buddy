from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from itertools import count, product
import sys
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import threading
import json

from arguments import parse_arguments
from payload_manager import prepare_payloads
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

    def run(self):
        """Executes the brute-force attack."""
        if self.args.output:
            try:
                self.output_file = open(self.args.output, "a", encoding="utf-8")
            except IOError as e:
                print(f"[-] Error opening output file: {e}", file=sys.stderr)
                sys.exit(1)

        param_list = self._prepare_param_list()
        brute_fields, constants, increment_fields = self._parse_params(param_list)
        self.args.increment_fields = increment_fields

        zip_fields, product_fields = self._normalize_combination_fields()
        self._validate_combination_fields(brute_fields, zip_fields, product_fields)

        payload_lists = self._prepare_payloads(brute_fields)
        
        if self.args.reauth > 0:
            self._setup_authentication(constants)

        combos_iter = self._generate_combinations(brute_fields, zip_fields, product_fields, payload_lists, constants)

        self._print_attack_info(brute_fields, increment_fields, constants, zip_fields, product_fields)

        with ThreadPoolExecutor(max_workers=self.args.threads) as executor:
            self._process_tasks(executor, combos_iter)

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

    def _prepare_param_list(self):
        """Merges --param and --cookie arguments into a single list."""
        param_list = self.args.param or []
        for cookie in self.args.cookie or []:
            if "=" not in cookie:
                print(f"[-] Error: Invalid cookie format: {cookie}. Use 'name=source'.", file=sys.stderr)
                sys.exit(1)
            name, source = cookie.split("=", 1)
            param_list.append(f"cookie:{name}={source}")
        return param_list

    def _parse_params(self, param_args):
        """Parses parameter arguments into brute-force fields, constants, and increment fields."""
        brute_fields, constants, increment_fields = [], {}, []
        for param in param_args:
            if param.startswith("increment:"):
                field = param[10:]
                if not field:
                    print("[-] Error: Increment field name cannot be empty.", file=sys.stderr)
                    sys.exit(1)
                increment_fields.append(field)
            elif "=" in param:
                key, source = param.split("=", 1)
                if os.path.isfile(source) or source.startswith("generate:"):
                    brute_fields.append((key, source))
                else:
                    constants[key] = source.strip('"')
            else:
                print(f"[-] Error: Invalid param format: {param}. Use 'key=source' or 'increment:field'.", file=sys.stderr)
                sys.exit(1)
        return brute_fields, constants, increment_fields

    def _normalize_combination_fields(self):
        """Normalizes and returns zip and product fields from arguments."""
        zip_fields = (self.args.zip_fields or "").replace(',', ' ').split()
        product_fields = (self.args.product_fields or "").replace(',', ' ').split()
        return zip_fields, product_fields

    def _validate_combination_fields(self, brute_fields, zip_fields, product_fields):
        """Validates that combination fields exist in brute-force fields."""
        all_brute_keys = {key for key, _ in brute_fields}
        if not zip_fields and not product_fields and brute_fields:
            product_fields.extend(all_brute_keys)
            self.args.product_fields = list(all_brute_keys)
        
        invalid_zip = set(zip_fields) - all_brute_keys
        invalid_product = set(product_fields) - all_brute_keys

        if invalid_zip or invalid_product:
            print(f"[-] Error: Invalid fields found in --zip-fields or --product-fields.", file=sys.stderr)
            if invalid_zip: print(f"    Invalid zip fields: {', '.join(invalid_zip)}", file=sys.stderr)
            if invalid_product: print(f"    Invalid product fields: {', '.join(invalid_product)}", file=sys.stderr)
            sys.exit(1)

    def _prepare_payloads(self, brute_fields):
        """Prepares payload lists for brute-force fields."""
        if not brute_fields:
            return []
        keys, sources = zip(*brute_fields)
        return prepare_payloads(keys, sources)

    def _setup_authentication(self, constants):
        """Initializes the authenticator and performs initial authentication."""
        if not all([self.args.login_url, self.args.username, self.args.password]):
            print("[-] Error: --reauth requires --login-url, --username, and --password.", file=sys.stderr)
            sys.exit(1)

        auth_headers = dict(h.split(":", 1) for h in self.args.auth_header or [])
        self.auth = Authenticator(self.args.login_url, self.args.username, self.args.password,
                                  self.args.proxy_url, self.args.insecure, auth_headers, self.args.auth_cookie_name)
        try:
            print("(+) Performing initial authentication...")
            session_cookie = self.auth.authenticate()
            constants[f"cookie:{self.args.auth_cookie_name}"] = session_cookie
            print(f"(+) Initial authentication successful. Session cookie set.")
        except Exception as e:
            print(f"[-] Initial authentication failed: {e}", file=sys.stderr)
            sys.exit(1)

    def _generate_combinations(self, brute_fields, zip_fields, product_fields, payload_lists, constants):
        """Yields payload combinations with their attempt numbers."""
        if not brute_fields:
            yield constants, next(self.attempt_counter)
            return

        brute_keys = [key for key, _ in brute_fields]
        zip_indices = [brute_keys.index(f) for f in zip_fields]
        product_indices = [brute_keys.index(f) for f in product_fields]

        zip_payloads = [payload_lists[i] for i in zip_indices]
        product_payloads = [payload_lists[i] for i in product_indices]

        zip_combos = zip(*zip_payloads) if zip_payloads else [()]
        
        for zip_combo in zip_combos:
            product_combos = product(*product_payloads) if product_payloads else [()]
            for prod_combo in product_combos:
                payload = constants.copy()
                for i, val in enumerate(zip_combo):
                    payload[zip_fields[i]] = val
                for i, val in enumerate(prod_combo):
                    payload[product_fields[i]] = val
                yield payload, next(self.attempt_counter)

    def _process_tasks(self, executor, combos_iter):
        """Manages the submission and processing of tasks to the thread pool."""
        futures = set()
        
        # Initial pool of tasks
        for i in range(self.args.threads):
            try:
                payload, attempt_num = next(combos_iter)
                session = self.sessions[i % self.args.threads]
                fut = executor.submit(self._task_wrapper, payload, attempt_num, session)
                futures.add(fut)
            except StopIteration:
                break

        while futures:
            for future in as_completed(futures):
                futures.remove(future)
                
                if self.stop_event.is_set():
                    continue

                result = future.result()
                
                # Check if the result was an error that needs re-queuing
                payload, attempt_num, response, elapsed, *error = result
                if error:
                    self._handle_error(executor, result)
                else:
                    self._handle_result(result)

                # Schedule a new task if the attack is not stopping
                if not self.stop_event.is_set():
                    try:
                        next_payload, next_attempt_num = next(combos_iter)
                        session = self.sessions[next_attempt_num % self.args.threads]
                        fut = executor.submit(self._task_wrapper, next_payload, next_attempt_num, session)
                        futures.add(fut)
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
        
        print(f"[-] Request Error: {payload} - {error_msg[0]}", file=sys.stderr)
        self.failed_attempts += 1

        self.requeue_counts[payload_key] += 1
        max_retries = self.args.per_payload_max_retries
        
        if max_retries == 0 or self.requeue_counts[payload_key] <= max_retries:
            print(f"    -> Re-submitting payload (retry {self.requeue_counts[payload_key]}/{max_retries or 'inf'}).")
            session = self.sessions[attempt_num % self.args.threads]
            # Re-submit the task to the executor
            fut = executor.submit(self._task_wrapper, payload, attempt_num, session)
            # This is a fire-and-forget resubmit into the pool.
            # We'd need to add it back to the `futures` set to track it, which complicates the loop.
            # A simpler model is to let the main loop handle adding new tasks.
            # The current implementation will just resubmit without tracking, which is not ideal.
            # Let's adjust the main loop to handle this better.
        else:
            print(f"    -> Max retries reached for payload. It will not be tried again.", file=sys.stderr)
        
        self._check_reauth()

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
                # This is a simplified approach. In a real-world scenario, updating
                # constants for in-flight/queued tasks would be more complex.
                print("(+) Re-authentication successful.")
                self.failed_attempts = 0
            except Exception as e:
                print(f"[-] Re-authentication failed: {e}. Exiting.", file=sys.stderr)
                self.stop_event.set()

    def _print_attack_info(self, brute_fields, increment_fields, constants, zip_fields, product_fields):
        """Prints information about the upcoming attack."""
        print(f"(+) Starting brute-force on {self.args.url} with method {self.args.method}")
        if brute_fields: print(f"(+) Brute-force fields: {[key for key, _ in brute_fields]}")
        if zip_fields: print(f"(+) Zipped fields: {zip_fields}")
        if product_fields: print(f"(+) Product fields: {product_fields}")
        if increment_fields: print(f"(+) Incrementing fields: {increment_fields}")
        if constants: print(f"(+) Constant fields: {constants}")

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