import argparse
import textwrap


def parse_arguments():
    """Parse and return command-line arguments."""
    parser = argparse.ArgumentParser(
        description="A user-friendly brute-force tool with re-authentication support.",
        epilog=textwrap.dedent('''\
            Examples:
              1. Basic username/password brute-force:
                 python run.py https://example.com/login \\
                   --param username=users.txt --param password="admin123" \\
                   --include-text 'Welcome' --threads 10

              2. MFA code generation with an incrementing header:
                 python run.py https://example.com/mfa \\
                   --param mfa-code=generate:0123456789:6 \\
                   --param increment:header:X-Request-ID --code 200 \\
                   --reauth 100 --login-url https://example.com/login \\
                   --username admin --password pass123

              3. Zipping usernames and passwords:
                 python run.py https://example.com/auth \\
                   --param username=users.txt --param password=passes.txt \\
                   --zip-fields username,password --exclude-text 'Invalid'
        '''),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Required arguments
    parser.add_argument("url", help="Target URL to brute-force.")

    # Parameter specifications
    param_group = parser.add_argument_group('Parameter Options')
    param_group.add_argument("--param", action="append",
                             help="Define a parameter for the request. Repeatable. Accepts file (user=users.txt), generated (code=generate:0-9:6), constant (role=guest), or increment (increment:field). Prefix with header:/cookie: to target headers/cookies.")
    param_group.add_argument("--cookie", action="append",
                             help="Shorthand for --param cookie:name=source.")
    param_group.add_argument("--zip-fields",
                             help="Comma-separated fields to zip together (e.g., username,password).")
    param_group.add_argument("--product-fields",
                             help="Comma-separated fields to combine in a product (default for all brute-force fields).")
    param_group.add_argument("--max-attempts", type=int, default=0,
                             help="Stop after this many attempts (0 for no limit).")

    # Authentication
    auth_group = parser.add_argument_group('Authentication')
    auth_group.add_argument("--login-url", help="URL for re-authentication.")
    auth_group.add_argument("--username", help="Username for re-authentication.")
    auth_group.add_argument("--password", help="Password for re-authentication.")
    auth_group.add_argument("--auth-header", action="append",
                            help="Custom header for authentication (e.g., 'Key:Value'). Can be specified multiple times.")
    auth_group.add_argument("--reauth", type=int, default=0,
                            help="Re-authenticate after this many consecutive failures (0 to disable).")
    auth_group.add_argument("--auth-cookie-name", default="session",
                            help="Cookie name to extract from auth response (default: session).")

    # Success criteria
    success_group = parser.add_argument_group('Success Criteria (first match wins)')
    # New, clearer flags
    success_group.add_argument("--include-text", help="Success if this text IS present in the response.")
    success_group.add_argument("--exclude-text", help="Success if this text is NOT present in the response.")
    # Backward-compatible (deprecated) aliases
    success_group.add_argument("--expect-text", help="[Deprecated: use --include-text] Text expected in the response for success.")
    success_group.add_argument("--text", help="[Deprecated: use --exclude-text] Text that should NOT be in the response for success.")
    success_group.add_argument("--regex", help="Regex pattern to match in the response for success.")
    success_group.add_argument("--code", type=int, help="HTTP status code for success.")
    success_group.add_argument("--length", type=int, help="Exact response body length for success.")
    success_group.add_argument("--time", type=float, help="Response time >= this value for success.")

    # Performance settings
    perf_group = parser.add_argument_group('Performance')
    perf_group.add_argument("--threads", type=int, default=10, help="Number of concurrent threads (default: 10).")
    perf_group.add_argument("--delay", type=float, default=0.0, help="Delay in seconds between requests (default: 0).")
    perf_group.add_argument("--retries", type=int, default=3, help="Retries for HTTP errors (e.g., 5xx) (default: 3).")
    perf_group.add_argument("--retry-backoff", type=float, default=0.2,
                            help="Backoff factor for retries (default: 0.2).")
    perf_group.add_argument("--per-payload-max-retries", type=int, default=5,
                            help="Max retries for a payload on network errors (e.g., timeout) (default: 5, 0 for unlimited).")

    # Network settings
    net_group = parser.add_argument_group('Network')
    net_group.add_argument("--proxy-url", help="Proxy URL (e.g., http://127.0.0.1:8080).")
    net_group.add_argument("--insecure", action="store_true", help="Skip SSL certificate verification.")
    net_group.add_argument("--method", default="POST", help="HTTP request method (default: POST).")
    net_group.add_argument("--timeout", type=float, default=10, help="Request timeout in seconds (default: 10).")
    net_group.add_argument("--json-body", action="store_true",
                           help="Send request body as JSON for POST/PUT/PATCH methods.")

    # Output settings
    output_group = parser.add_argument_group('Output')
    output_group.add_argument("-v", "--verbose", action="store_true", help="Show detailed output for all attempts.")
    output_group.add_argument("--output", help="File to save successful results to (JSON lines format).")
    output_group.add_argument("--stop-on-success", action="store_true",
                              help="Stop the attack after the first successful attempt.")

    args = parser.parse_args()

    # Backward-compatibility and deprecation notices for text flags
    if getattr(args, 'include_text', None) is None and getattr(args, 'expect_text', None):
        args.include_text = args.expect_text
        print("[!] --expect-text is deprecated; use --include-text instead.", flush=True)
    if getattr(args, 'exclude_text', None) is None and getattr(args, 'text', None):
        args.exclude_text = args.text
        print("[!] --text is deprecated; use --exclude-text instead.", flush=True)

    return args