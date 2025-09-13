def show_help():
    """Display the help menu with usage instructions and examples."""
    help_text = """
Brute Force Tool - A User-Friendly Brute-Forcing Utility

Usage:
  python run.py <url> [options]

Parameter Options:
  --param KEY=SOURCE    Parameter specification:
                        • Brute-force: key=file.txt or key=generate:chars:length
                        • Constant: key="value"
                        • Increment: increment:key
                        • Prefix with 'header:' or 'cookie:' for headers/cookies
  --cookie NAME=SOURCE  Cookie specification (e.g., session=cookies.txt)
  --zip-fields FIELD    Fields to combine with zip (e.g., username password)
  --product-fields FIELD Fields to combine with product (e.g., token)

Authentication:
  --login-url URL       URL for re-authentication
  --username USER       Username for re-authentication
  --password PASS       Password for re-authentication
  --auth-header KEY=VAL Custom header for authentication
  --reauth NUM          Re-authenticate after NUM failures (0 = disabled)

Success Criteria:
  --text TEXT           Text indicating failure (not present = success)
  --expect-text TEXT    Text indicating success (present = success)
  --regex PATTERN       Regex pattern indicating success (match = success)
  --code CODE           Success HTTP status code
  --length LENGTH       Success response length
  --time TIME           Minimum response time for success

Performance:
  --threads NUM         Number of threads (default: 5)
  --delay SEC           Delay between requests (default: 0.1s)
  --retries NUM         Retries for failed requests (default: 3)
  --timeout SEC         Request timeout in seconds (default: 20)

Network:
  --proxy-url URL       Proxy URL (e.g., http://127.0.0.1:8080)
  --insecure            Disable SSL verification
  --method METHOD       HTTP request method (default: POST)

Output:
  -v, --verbose         Show detailed output

Examples:
  1. Basic username/password brute-force:
     python run.py https://example.com/login \\
       --param username=users.txt --param password="admin123" \\
       --expect-text 'Welcome' --threads 10

  2. MFA code with incrementing header:
     python run.py https://example.com/mfa \\
       --param mfa-code=generate:0123456789:6 \\
       --param increment:header:X-Request-ID --code 200 \\
       --reauth 100 --login-url https://example.com/login \\
       --username admin --password pass123

  3. Cookie and header brute-force:
     python run.py https://example.com/api \\
       --cookie stay-logged-in=cookies.txt \\
       --param header:X-API-Key=keys.txt \\
       --zip-fields cookie:stay-logged-in \\
       --product-fields header:X-API-Key --regex 'Success.*'

  4. Zip username/password, product with token:
     python run.py https://example.com/auth \\
       --param username=users.txt --param password=passes.txt \\
       --param token=tokens.txt --zip-fields username password \\
       --product-fields token --text 'Invalid'

Tips:
  • Use --zip-fields and --product-fields to control combinations
  • Quote constants (e.g., "value"); use file.txt or generate: for brute-force
  • Enable --verbose for detailed logs
  • Start with fewer threads and increase based on target capacity
    """
    print(help_text)