import argparse
import textwrap

class HelpGuide(argparse.Action):
    """A custom action to show a detailed help guide."""
    def __init__(self, option_strings, dest, **kwargs):
        super(HelpGuide, self).__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        self.print_guide()
        parser.exit()

    def print_guide(self):
        """Prints the detailed help guide."""
        guide = textwrap.dedent("""
        =======================
        Brute Buddy - Full Guide
        =======================

        Brute Buddy is a versatile and robust tool for web application security testing.
        It simplifies complex brute-force attacks with support for multiple fields,
        dynamic payloads, and intelligent session handling.

        --------------
        Core Concepts
        --------------

        1. Payload Sources:
           Every parameter you test needs a source for its values. Brute Buddy supports three types:
           - File: A text file where each line is a payload.
             Example: --param username=users.txt
           - Generated: Create payloads on the fly. Ideal for numeric or simple character-based codes.
             Syntax: generate:<characters>:<length>
             Example: --param mfa_code=generate:0123456789:6  (generates all 6-digit codes)
           - Constant: A single, fixed value used for every request.
             Example: --param role="admin"

        2. Targeting Fields:
           By default, parameters are sent in the request body (for POST) or as URL parameters (for GET).
           You can target specific parts of the request using prefixes:
           - Header: --param header:X-API-Key=keys.txt
           - Cookie: --param cookie:session_id=sessions.txt (or use the --cookie shorthand)

        3. Combination Strategies:
           - Product Mode (Default): Tries every possible combination of payloads from the specified fields.
             This is the default behavior for all fields that are not part of a zip group.
             Example: --param user=users.txt --param pass=passes.txt
                      (Tries every user with every password)
           - Zip Mode: Pairs values from different files line-by-line. Useful when you have corresponding lists.
             Use --zip-fields to specify which fields to zip together.
             Example: --zip-fields username,password
                      (Tries users.txt[0] with passes.txt[0], users.txt[1] with passes.txt[1], etc.)

        --------------
        Command-Line Options
        --------------

        [+] Parameters and Payloads:
            url                     Target URL (required).
            --param <key=source>    Define a parameter. Can be used multiple times.
            --cookie <name=source>  Shorthand for --param cookie:name=source.
            --zip-fields <f1,f2>    Comma-separated fields to zip together.
            --product-fields <f1,f2> Comma-separated fields for product mode. Defaults to all non-zipped fields.
            --max-attempts <num>    Stop after N attempts (0 for no limit).

        [+] Authentication:
            --login-url <url>       URL for re-authentication.
            --username <user>       Username for re-authentication.
            --password <pass>       Password for re-authentication.
            --reauth <num>          Re-authenticate after N consecutive failures.
            --auth-header <K:V>     Extra header for authentication (e.g., 'Host:auth.site.com').
            --auth-cookie-name <n>  Session cookie name to extract (default: session).

        [+] Success Criteria (first match wins):
            --include-text <text>   Success if this text IS present in the response.
            --exclude-text <text>   Success if this text is NOT present in the response.
            --regex <pattern>       Success if the response body matches this regex pattern.
            --code <code>           Success if the HTTP status code matches.
            --length <len>          Success if the response body has this exact length.
            --time <seconds>        Success if the response time is >= this value.

        [+] Performance:
            --threads <num>         Number of concurrent threads (default: 10).
            --delay <seconds>       Delay between requests (default: 0).
            --retries <num>         Retries for HTTP errors (e.g., 5xx) (default: 3).
            --retry-backoff <f>     Backoff factor for retries (default: 0.2).
            --per-payload-max-retries <num> Max retries for a payload on network errors (default: 5).

        [+] Network:
            --method <method>       HTTP method (default: POST).
            --json-body             Send request body as JSON for POST/PUT/PATCH methods.
            --proxy-url <url>       Proxy URL (e.g., http://127.0.0.1:8080).
            --insecure              Skip SSL certificate verification.
            --timeout <seconds>     Request timeout (default: 10).

        [+] Output:
            -v, --verbose           Show detailed output for all attempts.
            --output <file>         File to save successful results to (JSON lines format).
            --stop-on-success       Stop after the first successful attempt.

        --------------
        Examples
        --------------

        1. Basic Login Brute-Force:
           Try all usernames from a file with all passwords from another file.
           $ python run.py https://example.com/login \\
               --param username=users.txt \\
               --param password=passes.txt \\
               --include-text "Welcome"

        2. Zipping Usernames and Passwords:
           Try username/password pairs from corresponding lines in two files.
           $ python run.py https://example.com/login \\
               --param username=users.txt \\
               --param password=passes.txt \\
               --zip-fields "username,password" \\
               --exclude-text "Invalid credentials"

        3. Brute-Forcing a Header API Key:
           Try a list of API keys in a custom header.
           $ python run.py https://api.example.com/v1/user \\
               --method GET \\
               --param header:X-Api-Key=keys.txt \\
               --code 200

        4. Re-authentication and MFA Code Generation:
           Log in, then brute-force 6-digit MFA codes, re-authenticating every 100 failures.
           $ python run.py https://example.com/mfa-check \\
               --param code=generate:0123456789:6 \\
               --reauth 100 \\
               --login-url https://example.com/login \\
               --username "admin" --password "admin123" \\
               --code 200 \\
               --output successful_codes.jsonl
        """)
        print(guide)
