from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import count, product
from arguments import parse_arguments
from payload_manager import prepare_payloads
from request_manager import make_attempt, check_success
from authenticator import Authenticator
from help_guide import show_help
import sys
import requests
from requests.adapters import HTTPAdapter
import os
import threading
import json


def parse_params(param_args):
    """Parse --param arguments into brute-force fields, constants, and increment fields."""
    brute_fields, constants, increment_fields = [], {}, []
    
    for param in param_args or []:
        if not param:
            print("[-] Error: Empty parameter provided")
            sys.exit(1)
            
        if param.startswith("increment:"):
            field = param[10:]
            if not field:
                print("[-] Error: Increment field name cannot be empty")
                sys.exit(1)
            increment_fields.append(field)
        elif "=" not in param:
            print(f"[-] Error: Invalid param format: {param}. Use 'key=source' or 'increment:field'")
            sys.exit(1)
        else:
            key, source = param.split("=", 1)
            if not key or not source:
                print(f"[-] Error: Key or source cannot be empty in param: {param}")
                sys.exit(1)
                
            if source.startswith("generate:"):
                brute_fields.append((key, source))
            elif os.path.isfile(source):
                brute_fields.append((key, source))
            else:
                # Treat as constant (quoted or unquoted)
                constants[key] = source.strip('"')  # Remove quotes if present, otherwise use as-is
                
    return brute_fields, constants, increment_fields


def setup_sessions(num_threads, retries):
    """Create optimized session pool."""
    sessions = []
    adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=num_threads)
    
    for _ in range(num_threads):
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        sessions.append(session)
    
    return sessions


def validate_combination_fields(brute_fields, zip_fields, product_fields):
    """Validate and setup combination fields."""
    all_brute_keys = {key for key, _ in brute_fields}
    invalid_zip = set(zip_fields) - all_brute_keys
    invalid_product = set(product_fields) - all_brute_keys
    
    if invalid_zip or invalid_product:
        print(f"[-] Error: Invalid fields in --zip-fields ({invalid_zip}) or --product-fields ({invalid_product})")
        sys.exit(1)
    
    # Default to product for unspecified fields
    if not zip_fields and not product_fields and brute_fields:
        product_fields = list(all_brute_keys)
    
    return product_fields


def generate_combinations_iter(brute_fields, zip_fields, product_fields, payload_lists):
    """Yield parameter combinations without materializing all in memory."""
    zip_indices = [i for i, (key, _) in enumerate(brute_fields) if key in zip_fields]
    product_indices = [i for i, (key, _) in enumerate(brute_fields) if key in product_fields]

    zip_payloads = [payload_lists[i] for i in zip_indices] if zip_indices else []
    product_payloads = [payload_lists[i] for i in product_indices] if product_indices else []

    zip_combos_iter = zip(*zip_payloads) if zip_payloads else [()]
    for zip_combo in zip_combos_iter:
        if product_payloads:
            for prod_combo in product(*product_payloads):
                yield zip_combo, prod_combo, zip_indices, product_indices
        else:
            yield zip_combo, (), zip_indices, product_indices

def _normalize_fields_list(lst):
    """Normalize list arguments that may contain comma/space separated items."""
    if not lst:
        return []
    out = []
    for item in lst:
        # split on commas and whitespace
        for token in filter(None, [t.strip() for part in item.split(',') for t in part.split()]):
            out.append(token)
    return out


def setup_authentication(args):
    """Setup initial authentication if required."""
    if args.reauth <= 0:
        return None, {}
    
    if not all([args.login_url, args.username, args.password]):
        print("[-] Error: --reauth requires --login-url, --username, and --password")
        sys.exit(1)
    
    # Parse auth headers if provided as list of "Key=Value"
    auth_headers = {}
    for h in args.auth_header or []:
        if "=" not in h:
            print(f"[-] Error: Invalid --auth-header format: {h}. Use KEY=VALUE")
            sys.exit(1)
        k, v = h.split("=", 1)
        auth_headers[k.strip()] = v.strip()

    auth = Authenticator(args.login_url, args.username, args.password, 
                        args.proxy_url, args.insecure, auth_headers, args.auth_cookie_name)
    
    try:
        session_cookie = auth.authenticate()
        constants = {"cookie:session": session_cookie}
        print(f"(+) Initial authentication successful, session cookie: {session_cookie}")
        return auth, constants
    except Exception as e:
        print(f"[-] Initial authentication failed: {e}")
        sys.exit(1)


def run_brute_force():
    """Run the brute-force attack with the provided arguments."""
    if len(sys.argv) == 1 or "--help" in sys.argv:
        show_help()
        sys.exit(0)

    args = parse_arguments()
    param_list = args.param or []
    
    # Convert cookies to parameters
    for cookie in args.cookie or []:
        if "=" not in cookie:
            print(f"[-] Error: Invalid cookie format: {cookie}. Use 'name=value' or 'name=file.txt'")
            sys.exit(1)
        name, source = cookie.split("=", 1)
        param_list.append(f"cookie:{name}={source}")

    # Parse parameters
    brute_fields, constants, increment_fields = parse_params(param_list)
    zip_fields = _normalize_fields_list(args.zip_fields)
    product_fields = _normalize_fields_list(args.product_fields)

    # Validate and setup combination fields
    product_fields = validate_combination_fields(brute_fields, zip_fields, product_fields)

    # Prepare payloads
    if brute_fields:
        payload_sources = [source for _, source in brute_fields]
        payload_lists = prepare_payloads([key for key, _ in brute_fields], payload_sources)
        if not payload_lists:
            print("[-] Error: No valid payloads generated. Check payload files or specifications.")
            sys.exit(1)
    else:
        payload_lists = []

    # Create combinations iterator (streaming)
    combos_iter = None
    if brute_fields:
        combos_iter = generate_combinations_iter(brute_fields, zip_fields, product_fields, payload_lists)
        # Estimate total attempts safely if lists are small (<= 50k combinations), else keep unknown
        try:
            # Compute sizes without loading all combos at once
            sizes = {key: len(payload) for key, payload in zip([k for k, _ in brute_fields], payload_lists)}
            zip_size = None
            if zip_fields:
                zip_size = min(sizes[k] for k in zip_fields)
            product_size = 1
            if product_fields:
                for k in product_fields:
                    product_size *= sizes[k]
            base = (zip_size if zip_size is not None else 1) * (product_size if product_size else 1)
            total_attempts = base if base <= 50000 else None
        except Exception:
            total_attempts = None
    else:
        total_attempts = 1

    # Setup authentication
    auth, auth_constants = setup_authentication(args)
    constants.update(auth_constants)

    # Initialize counters and display info
    attempt_counter = count(1)
    # total_attempts maybe unknown when streaming

    print(f"(+) Starting brute-force on {args.url} with method {args.method}")
    if brute_fields:
        print(f"(+) Brute-force fields: {[key for key, _ in brute_fields]}")
        if zip_fields:
            print(f"(+) Zipped fields: {zip_fields}")
        if product_fields:
            print(f"(+) Product fields: {product_fields}")
    if increment_fields:
        print(f"(+) Increment fields: {increment_fields}")
    if constants:
        print(f"(+) Constant fields: {constants}")

    # Setup session pool
    sessions = setup_sessions(args.threads, args.retries)
    successes = []
    attempt_count = failed_attempts = 0
    stop_event = threading.Event()
    output_file = None
    try:
        if args.output:
            output_file = open(args.output, "a", encoding="utf-8")
    except Exception as e:
        print(f"[-] Could not open output file {args.output}: {e}")
        sys.exit(1)

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        pending = set()
        scheduled = 0

        def schedule_one(values):
            nonlocal scheduled
            session = sessions[scheduled % args.threads]
            fut = executor.submit(
                make_attempt, args.url, values, increment_fields,
                next(attempt_counter), args, auth, session
            )
            pending.add(fut)
            scheduled += 1

        if combos_iter is None:
            schedule_one(constants)
        else:
            # Pre-schedule up to threads to fill the pool
            try:
                for _ in range(args.threads):
                    zip_combo, product_combo, zip_indices, product_indices = next(combos_iter)
                    field_values = {}
                    for i, value in zip(zip_indices, zip_combo):
                        field_values[brute_fields[i][0]] = value
                    for i, value in zip(product_indices, product_combo):
                        field_values[brute_fields[i][0]] = value
                    schedule_one({**constants, **field_values})
            except StopIteration:
                pass

        if scheduled and total_attempts is None:
            print(f"(+) Scheduled initial batch of {min(scheduled, args.threads)} attempts (streaming mode)")
        elif scheduled:
            print(f"(+) Total attempts scheduled: {scheduled}")

        while pending:
            # Wait for any future to complete
            for future in as_completed(list(pending), timeout=None):
                pending.remove(future)
                result = future.result()
            attempt_count += 1
            if args.verbose:
                if total_attempts:
                    print(f"(+) Attempt {attempt_count}/{total_attempts}")
                else:
                    print(f"(+) Attempt {attempt_count}")

            if len(result) == 5:  # Error case
                combo, _, _, _, error = result
                print(f"[-] Request failed for {combo} — {error}")
                failed_attempts += 1
                continue

            combo, counter_val, response, elapsed = result
            if check_success(response, elapsed, args):
                print(f"[+] SUCCESS — {combo}")
                print(f"    Status: {response.status_code}, Time: {elapsed:.2f}s, Length: {len(response.text)}")
                if args.verbose:
                    print(f"    Response preview:\n{response.text[:300]}\n")
                successes.append(combo)
                if output_file:
                    try:
                        output_file.write(json.dumps({"combo": combo, "status": response.status_code, "time": elapsed, "length": len(response.text)}) + "\n")
                        output_file.flush()
                    except Exception as e:
                        print(f"[-] Failed to write to output file: {e}")
                failed_attempts = 0
                if args.stop_on_success:
                    stop_event.set()
                    # Attempt to cancel remaining futures
                    for f in list(pending):
                        f.cancel()
                    pending.clear()
                    break
            else:
                failed_attempts += 1
                if args.verbose:
                    print(f"[-] Failed — {combo} (Status: {response.status_code}, Time: {elapsed:.2f}s, Length: {len(response.text)})")

            # Re-authentication logic
            if args.reauth > 0 and failed_attempts >= args.reauth and not successes:
                print(f"(+) Re-authenticating after {failed_attempts} failed attempts")
                try:
                    session_cookie = auth.authenticate()
                    constants["cookie:session"] = session_cookie
                    print(f"(+) Re-authentication successful, new session cookie: {session_cookie}")
                    failed_attempts = 0
                except Exception as e:
                    print(f"[-] Re-authentication failed: {e}")
                    sys.exit(1)

            # Max attempts guard
            if args.max_attempts and attempt_count >= args.max_attempts:
                print(f"(+) Reached max attempts limit: {args.max_attempts}")
                # Attempt to cancel remaining and exit loop
                for f in list(pending):
                    f.cancel()
                pending.clear()
                break

            # Keep scheduling next items while not stopping
            if combos_iter and not stop_event.is_set():
                try:
                    zip_combo, product_combo, zip_indices, product_indices = next(combos_iter)
                    field_values = {}
                    for i, value in zip(zip_indices, zip_combo):
                        field_values[brute_fields[i][0]] = value
                    for i, value in zip(product_indices, product_combo):
                        field_values[brute_fields[i][0]] = value
                    schedule_one({**constants, **field_values})
                except StopIteration:
                    pass
            # If we broke due to stop/max, exit outer while
            if stop_event.is_set() or (args.max_attempts and attempt_count >= args.max_attempts):
                break

    # Cleanup and results
    for session in sessions:
        session.close()
    
    if auth:
        auth.close()
    if output_file:
        output_file.close()

    if not successes:
        print("(-) No successful combinations found.")
    else:
        print("(+) Successful combinations:")
        for combo in successes:
            print(f"    {combo}")


if __name__ == "__main__":
    run_brute_force()