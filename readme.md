# Brute Buddy

Brute Buddy is a fast, flexible CLI for web app security testing. It makes complex brute-force scenarios simple: multi-field payloads, generated values, zipped/product combinations, headers/cookies, and smart re-authentication.

---

## Quick start

Try a basic login brute-force on a test endpoint. This tries every username in `users.txt` with a constant password.

```bash
# Create a dummy users.txt file
echo "admin" > users.txt
echo "user"  >> users.txt
echo "test"  >> users.txt

# Run the attack
python run.py https://httpbin.org/post \
  --param username=users.txt \
  --param password="password123" \
  --include-text "password123" \
  --threads 5
```

---

## Install

1) Python 3.10+
2) Install dependencies:
```bash
pip install -r requirements.txt
```
3) Show all options:
```bash
python run.py --help
```

---

## How it works (in 60 seconds)

- You define parameters with `--param key=source`.
- Sources can be:
  - A file: `username=users.txt` (one value per line)
  - Generated: `code=generate:0123456789:6` (all 6-digit codes)
  - Constant: `role=admin`
  - Incrementing: `increment:id` (uses attempt counter)
- Target where each param goes:
  - Body/URL (default): `username=users.txt`
  - Header: `header:X-Api-Key=keys.txt`
  - Cookie: `cookie:session=values.txt` or shorthand `--cookie session=values.txt`
- Combine fields:
  - Product mode (default): try every combination.
  - Zip mode: pair fields by index with `--zip-fields "field1,field2"`.

If you don’t specify `--product-fields` or `--zip-fields`, all brute-force fields are combined in product mode by default.

---

## Defining parameters (all the ways)

- Constant value (used every request):
```bash
--param role="admin"
```

- Wordlist from file:
```bash
--param username=users.txt
```

- Generated values (chars:length):
```bash
--param code=generate:0123456789:6
```

- Target a header or cookie:
```bash
--param header:X-Api-Key=keys.txt
--param cookie:session_id=sessions.txt
# or shorthand for cookies
--cookie session_id=sessions.txt
```

- Incrementing fields (use attempt counter as value):
```bash
--param increment:request_id
--param increment:header:X-Request-ID
--param increment:cookie:visit
```

---

## Combining fields: product vs. zip

- Product (default): every combination.
```bash
--param username=users.txt --param password=passes.txt
# Equivalent explicit form:
--product-fields "username password"
```

- Zip: pair fields by index (line 1 with line 1, etc.).
```bash
--zip-fields "username,password"
```

- Mix zip and product:
```bash
--zip-fields "username,password" --product-fields "mfa_code"
```

Tips:
- Field lists accept commas or spaces: `"a,b"` or `"a b"`.
- If you use only constants (no wordlists/generators), use `--max-attempts` to limit attempts.

---

## Success criteria (first match wins)

Pick one or more. The first satisfied condition marks success.

- Include text:
```bash
--include-text "Welcome"
```

- Exclude text:
```bash
--exclude-text "Invalid credentials"
```

- Regex match:
```bash
--regex "Success: [A-Z0-9]{6}"
```

- HTTP status code:
```bash
--code 200
```

- Exact length or minimum time:
```bash
--length 1234
--time 0.8
```

Stop on first success and save results:
```bash
--stop-on-success --output hits.jsonl
```

---

## Authentication & re-authentication

When the target flow requires a session cookie that expires (e.g., MFA step), enable re-auth:

```bash
--reauth 100 \
--login-url https://example.com/login \
--username carlos \
--password montoya \
--auth-cookie-name session \
--auth-header "Host: example.com"   # optional, repeatable
```

Notes:
- The tool logs in via POST to `--login-url` with `username` and `password` form fields.
- It extracts the cookie named by `--auth-cookie-name` (default: `session`) and applies it to all threads.
- After `--reauth` consecutive failures, it re-authenticates automatically and refreshes the cookie.

---

## Networking

- Methods and body format:
```bash
--method GET|POST|PUT|PATCH
--json-body    # send JSON for POST/PUT/PATCH; otherwise form-encoded
```

- Proxy and TLS:
```bash
--proxy-url http://127.0.0.1:8080
--insecure                  # skip TLS verification
--timeout 10                # seconds per request
```

---

## Performance & reliability

- Concurrency and pacing:
```bash
--threads 10
--delay 0.0
```

- Automatic retries:
```bash
--retries 3                 # HTTP 5xx/429 adapter retries
--retry-backoff 0.2
--per-payload-max-retries 5 # network errors; 0 = unlimited
```

---

## Output

- Verbose logs:
```bash
-v
```

- Write successes to JSONL file:
```bash
--output results.jsonl
```

- Stop after first success:
```bash
--stop-on-success
```

Each success record includes the payload, status, elapsed time, and response length.

---

## End-to-end examples

1) Username/password brute-force (form POST)
```bash
python run.py https://example.com/login \
  --param username=usernames.txt \
  --param password=passwords.txt \
  --include-text "Welcome" \
  --threads 10
```

2) Zip username/password pairs
```bash
python run.py https://example.com/login \
  --param username=users.txt \
  --param password=passes.txt \
  --zip-fields "username,password" \
  --exclude-text "Invalid credentials"
```

3) Header API key brute-force (GET)
```bash
python run.py https://api.example.com/v1/me \
  --method GET \
  --param header:X-Api-Key=keys.txt \
  --code 200
```

4) MFA: zip user/pass, product MFA codes
```bash
python run.py https://example.com/login-mfa \
  --param username=users.txt \
  --param password=passes.txt \
  --param mfa_code=generate:0123456789:6 \
  --zip-fields "username,password" \
  --product-fields "mfa_code" \
  --code 200
```

5) Re-authenticate every 100 failures and save hits
```bash
python run.py https://example.com/mfa-check \
  --param code=generate:0123456789:6 \
  --reauth 100 \
  --login-url https://example.com/login \
  --username "admin" --password "admin123" \
  --code 200 \
  --stop-on-success \
  --output successful_codes.jsonl
```

6) JSON body change-password request (with session cookie)
```bash
python run.py https://example.com/my-account/change-password \
  --param username="carlos" \
  --param current-password=pass.txt \
  --param new-password-1="x" \
  --param new-password-2="y" \
  --json-body \
  --cookie session=YOUR_SESSION_COOKIE \
  --include-text "New passwords do not match"
```

7) Add an incrementing request ID header on each attempt
```bash
python run.py https://example.com/login \
  --param username=users.txt \
  --param password=passes.txt \
  --param increment:header:X-Request-ID \
  --code 302
```

---

## Tips & troubleshooting

- Field lists accept commas or spaces.
- For GET requests, body params are sent as URL query params.
- If your payload files are huge, consider narrowing with `--zip-fields` where pairs are known.
- Proxy timeouts: lower `--timeout`, reduce `--threads`, or increase `--per-payload-max-retries`.
- If you only use constants, set `--max-attempts` to limit the run.

---

## Legal

Use this tool responsibly and only against systems you’re authorized to test.

---

## License

MIT
