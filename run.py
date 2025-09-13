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


def generate_combinations(brute_fields, zip_fields, product_fields, payload_lists):
    """Generate all parameter combinations efficiently."""
    zip_indices = [i for i, (key, _) in enumerate(brute_fields) if key in zip_fields]
    product_indices = [i for i, (key, _) in enumerate(brute_fields) if key in product_fields]
    
    zip_payloads = [payload_lists[i] for i in zip_indices] if zip_indices else []
    product_payloads = [payload_lists[i] for i in product_indices] if product_indices else []
    
    zip_combos = list(zip(*zip_payloads)) if zip_payloads else [()]
    product_combos = list(product(*product_payloads)) if product_payloads else [()]
    
    return list(product(zip_combos, product_combos)), zip_indices, product_indices


def setup_authentication(args):
    """Setup initial authentication if required."""
    if args.reauth <= 0:
        return None, {}
    
    if not all([args.login_url, args.username, args.password]):
        print("[-] Error: --reauth requires --login-url, --username, and --password")
        sys.exit(1)
    
    auth = Authenticator(args.login_url, args.username, args.password, 
                        args.proxy_url, args.insecure, args.auth_header or {})
    
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
    zip_fields = args.zip_fields or []
    product_fields = args.product_fields or []

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

    # Generate combinations
    all_combinations, zip_indices, product_indices = generate_combinations(
        brute_fields, zip_fields, product_fields, payload_lists)

    # Setup authentication
    auth, auth_constants = setup_authentication(args)
    constants.update(auth_constants)

    # Initialize counters and display info
    attempt_counter = count(1)
    total_attempts = len(all_combinations) if all_combinations else 1

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

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = []
        
        if not all_combinations:
            futures.append(executor.submit(
                make_attempt, args.url, constants, increment_fields, 
                next(attempt_counter), args, auth, sessions[0]
            ))
        else:
            for zip_combo, product_combo in all_combinations:
                field_values = {}
                for i, value in zip(zip_indices, zip_combo):
                    field_values[brute_fields[i][0]] = value
                for i, value in zip(product_indices, product_combo):
                    field_values[brute_fields[i][0]] = value
                
                all_values = {**constants, **field_values}
                session = sessions[len(futures) % args.threads]
                futures.append(executor.submit(
                    make_attempt, args.url, all_values, increment_fields, 
                    next(attempt_counter), args, auth, session
                ))

        print(f"(+) Total attempts scheduled: {len(futures)}")

        for future in as_completed(futures):
            attempt_count += 1
            if args.verbose:
                print(f"(+) Attempt {attempt_count}/{total_attempts}")
            
            result = future.result()

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
                failed_attempts = 0
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

    # Cleanup and results
    for session in sessions:
        session.close()
    
    if auth:
        auth.close()

    if not successes:
        print("(-) No successful combinations found.")
    else:
        print("(+) Successful combinations:")
        for combo in successes:
            print(f"    {combo}")


if __name__ == "__main__":
    run_brute_force()