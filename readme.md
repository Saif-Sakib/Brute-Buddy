# Brute Buddy

# Brute Buddy

Brute Buddy is a versatile and robust CLI for web app security testing. It makes complex brute-force scenarios simple: multi-field brute-forcing, dynamic payloads, and smart session handling for forms, APIs, headers, and cookies.

---

## Quick Start

Try a basic login brute-force on a test endpoint. This finds a valid username from `users.txt` with a constant password.

```bash
# Create a dummy users.txt file
echo "admin" > users.txt
echo "user" >> users.txt
echo "test" >> users.txt

# Run the attack
python run.py https://httpbin.org/post \
  --param username=users.txt \
  --param password="password123" \
  --include-text "password123" \
  --threads 5
```

---

## Installation

1.  Ensure you have Python 3.10+ installed.
2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  You're ready to go!

---

## Usage

For a quick overview of the commands, use the standard help flag:

```bash
python run.py --help
```

For a comprehensive guide with detailed explanations and examples of all features, use the `--help-guide` flag:

```bash
python run.py --help-guide
```

This guide covers core concepts like:
-   **Payload Sources** (files, generated, constants)
-   **Targeting Fields** (body, headers, cookies)
-   **Combination Strategies** (product vs. zip)
-   **Advanced Features** like re-authentication and performance tuning.

---

## License

This project is licensed under the MIT License.
````markdown
# Brute Buddy

Brute Buddy is a versatile and robust CLI for web app security testing. It makes complex brute-force scenarios simple: multi-field brute-forcing, dynamic payloads, and smart session handling for forms, APIs, headers, and cookies.

---

## Quick start

Try a basic login brute-force on a test endpoint. This finds a valid username from `users.txt` with a constant password.

```bash
# Create a dummy users.txt file
echo "admin" > users.txt
echo "user" >> users.txt
echo "test" >> users.txt

# Run the attack
python run.py https://httpbin.org/post \
  --param username=users.txt \
  --param password="password123" \
  --include-text "password123" \
  --threads 5
```

---

## Core concepts

### 1) Payload sources

Every field you test needs a payload source:

- File: `--param username=users.txt` (one value per line)
- Generated: `--param mfa_code=generate:0123456789:6` (all 6-digit codes)
- Constant: `--param role="admin"`

### 2) Targeting fields

Add a prefix to target where the param goes:

- Body/URL param (default): `--param username=users.txt`
- Header: `--param header:X-API-Key=keys.txt`
- Cookie: `--param cookie:session_id=sessions.txt` or `--cookie session_id=sessions.txt`

### 3) Combination strategies

- Product mode (default): try every combination. Use `--product-fields` to list fields (defaults to all brute-force fields).
- Zip mode: pair values by index across fields. Use `--zip-fields` to list fields to zip.

---

## Command-line options (friendly summary)

### Parameters and payloads
- `url`: Target URL (required)
- `--param <key=source>`: Define a parameter. Repeatable.
- `--cookie <name=source>`: Shorthand for `--param cookie:name=source`.
- `--zip-fields <field1,field2>`: Comma-separated fields to zip.
- `--product-fields <field1,field2>`: Comma-separated fields for product mode; defaults to all brute-force fields.
- `--max-attempts <num>`: Stop after N attempts (0 = no limit).

### Authentication
- `--login-url <url>`: URL for re-authentication.
- `--username <user>` / `--password <pass>`: Credentials for re-auth.
- `--reauth <num>`: Re-authenticate after N consecutive failures.
- `--auth-header <Key:Value>`: Extra header(s) for auth (repeatable).
- `--auth-cookie-name <name>`: Session cookie name to extract (default: `session`).

### Success criteria (first match wins)
- `--include-text <text>`: Succeeds if text IS present.
- `--exclude-text <text>`: Succeeds if text is NOT present.
- Deprecated aliases still work with a notice: `--expect-text`, `--text`.
- `--regex <pattern>`: Response matches regex.
- `--code <code>`: HTTP status code matches.
- `--length <len>`: Exact body length.
- `--time <seconds>`: Response time >= value.

### Performance
- `--threads <num>`: Concurrent threads (default: 10).
- `--delay <seconds>`: Delay between requests (default: 0).
- `--retries <num>`: Adapter retries for HTTP 5xx, 429, etc. (default: 3).
- `--per-payload-max-retries <num>`: Max re-queues on network errors (default: 5; 0 = unlimited).

### Network
- `--method <method>`: HTTP method (default: POST).
- `--json-body`: Send parameters as JSON for POST/PUT/PATCH.
- `--proxy-url <url>`: Proxy (e.g., http://127.0.0.1:8080).
- `--insecure`: Skip TLS verification.
- `--timeout <seconds>`: Request timeout (default: 10).

### Output
- `-v, --verbose`: Per-attempt logs.
- `--output <file>`: Write successes (JSONL).
- `--stop-on-success`: Stop after first success.

---

## Examples

1) Basic username/password brute-force
```bash
python run.py https://example.com/login \
  --param username=usernames.txt \
  --param password=passwords.txt \
  --include-text "Welcome" \
  --threads 10
```
# Brute Buddy

Brute Buddy is a versatile and robust CLI for web app security testing. It makes complex brute-force scenarios simple: multi-field brute-forcing, dynamic payloads, and smart session handling for forms, APIs, headers, and cookies.

---

## Quick start

Try a basic login brute-force on a test endpoint. This finds a valid username from `users.txt` with a constant password.

```bash
# Create a dummy users.txt file
echo "admin" > users.txt
echo "user" >> users.txt
echo "test" >> users.txt

# Run the attack
python run.py https://httpbin.org/post \
  --param username=users.txt \
  --param password="password123" \
  --include-text "password123" \
  --threads 5
```

---

## Core concepts

1) Payload sources
- File: `--param username=users.txt` (one value per line)
- Generated: `--param mfa_code=generate:0123456789:6` (all 6-digit codes)
- Constant: `--param role="admin"`

2) Targeting fields
- Body/URL param (default): `--param username=users.txt`
- Header: `--param header:X-API-Key=keys.txt`
- Cookie: `--param cookie:session_id=sessions.txt` or `--cookie session_id=sessions.txt`

3) Combination strategies
- Product mode (default): try every combination. Use `--product-fields` to list fields (defaults to all brute-force fields).
- Zip mode: pair values by index across fields. Use `--zip-fields` to list fields to zip.

---

## Command-line options (friendly summary)

See `python run.py --help` for the complete list, or `python run.py --help-guide` for an extended guide with examples.

- Parameters and payloads: `--param`, `--cookie`, `--zip-fields`, `--product-fields`, `--max-attempts`
- Authentication: `--login-url`, `--username`, `--password`, `--reauth`, `--auth-header`, `--auth-cookie-name`
- Success criteria: `--include-text`, `--exclude-text`, `--regex`, `--code`, `--length`, `--time`
- Performance: `--threads`, `--delay`, `--retries`, `--retry-backoff`, `--per-payload-max-retries`
- Network: `--method`, `--json-body`, `--proxy-url`, `--insecure`, `--timeout`
- Output: `--verbose`, `--output`, `--stop-on-success`

---

## Examples

1) Username/password brute-force
```bash
python run.py https://example.com/login \
  --param username=usernames.txt \
  --param password=passwords.txt \
  --include-text "Welcome" \
  --threads 10
```

2) Zipping usernames and passwords
```bash
python run.py https://example.com/login \
  --param username=users.txt \
  --param password=passes.txt \
  --zip-fields "username,password" \
  --exclude-text "Invalid credentials"
```

3) Header API key brute-force
```bash
python run.py https://api.example.com/v1/user \
  --method GET \
  --param header:X-Api-Key=keys.txt \
  --code 200
```

4) Re-authentication + save output
```bash
python run.py https://example.com/mfa-check \
  --param code=generate:0123456789:6 \
  --reauth 100 \
  --login-url https://example.com/login \
  --username "admin" --password "admin123" \
  --code 200 \
  --output successful_codes.jsonl
```

---

## Installation

1) Python 3.10+
2) Install dependencies:
```bash
pip install -r requirements.txt
```
3) Show help:
```bash
python run.py --help
```

---

## Troubleshooting

- Proxy timeouts: adjust `--per-payload-max-retries`, `--retries`, and `--retry-backoff`.
- With timeouts, verbose output may be delayed until attempts complete.
- Try without a proxy and with a shorter `--timeout` to isolate issues.

---

## License

MIT
