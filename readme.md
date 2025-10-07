# Brute Buddy

# Brute Buddy

Brute Buddy is a versatile and robust tool for web application security testing, designed to make complex brute-force attacks simple and effective. It supports multi-field brute-forcing, dynamic payload generation, and intelligent session handling, making it ideal for testing login forms, API endpoints, and more.

---

## Quick Start

Try a basic login brute-force on a test endpoint. This command attempts to find a valid username from `users.txt` using a single, constant password.

```bash
# Create a dummy users.txt file
echo "admin" > users.txt
echo "user" >> users.txt
echo "test" >> users.txt

# Run the attack
python run.py https://httpbin.org/post \
  --param username=users.txt \
  --param password="password123" \
  --expect-text "password123" \
  --threads 5
```

---

## Core Concepts

### 1. Payload Sources

Every parameter or cookie you test needs a source for its values (payloads). Brute Buddy supports three types:

-   **File**: A simple text file where each line is a payload.
    -   `--param username=users.txt`
-   **Generated**: Create payloads on the fly. Excellent for numeric or simple character-based codes.
    -   `--param mfa_code=generate:0123456789:6` (generates all 6-digit codes)
-   **Constant**: A single, fixed value.
    -   `--param role="admin"`

### 2. Targeting Fields

You can target different parts of an HTTP request by adding a prefix to your parameter key:

-   **Body/URL Parameter** (default): No prefix needed.
    -   `--param username=users.txt`
-   **HTTP Header**: Use the `header:` prefix.
    -   `--param header:X-API-Key=keys.txt`
-   **Cookie**: Use the `cookie:` prefix or the `--cookie` shorthand.
    -   `--param cookie:session_id=sessions.txt`
    -   `--cookie session_id=sessions.txt`

### 3. Combination Strategies

When you provide multiple brute-force fields, you need to tell Brute Buddy how to combine them.

-   **Product Mode** (default): Tries **every possible combination**. If you have 10 usernames and 10 passwords, it will make 100 requests. Use `--product-fields` to specify which fields to include.
-   **Zip Mode**: Pairs payloads from different sources. The first username is tried with the first password, the second with the second, and so on. The attack stops when the shortest list runs out. Use `--zip-fields` to specify which fields to pair.

---

## Features & Command-Line Options

### Parameters and Payloads
-   `url`: The target URL (required).
-   `--param <key=source>`: Defines a parameter. Can be used multiple times.
-   `--cookie <name=source>`: Shorthand for `--param cookie:name=source`.
-   `--zip-fields <field1,field2>`: Comma-separated fields to "zip" together.
-   `--product-fields <field1,field2>`: Comma-separated fields for product combination. If no combination strategy is set, all fields are used in product mode.
-   `--max-attempts <num>`: Stop after a certain number of attempts.

### Authentication
-   `--login-url <url>`: URL for re-authentication if a session expires.
-   `--username <user>` / `--password <pass>`: Credentials for re-authentication.
-   `--reauth <num>`: Re-authenticate after `num` consecutive failures.
-   `--auth-header <Key:Value>`: Custom header to send with authentication requests.
-   `--auth-cookie-name <name>`: The name of the session cookie to extract after login.

### Success Criteria (First Match Wins)
-   `--expect-text <text>`: Success if this text is **found** in the response.
-   `--text <text>`: Success if this text is **not found** in the response.
-   `--regex <pattern>`: Success if this regex pattern matches the response.
-   `--code <code>`: Success if the HTTP status code matches.
-   `--length <len>`: Success if the response body has this exact length.
-   `--time <seconds>`: Success if the response takes at least this long.

### Performance
-   `--threads <num>`: Number of concurrent threads (default: 10).
-   `--delay <seconds>`: Delay between each request (default: 0).
-   `--retries <num>`: Retries for HTTP server errors (e.g., 5xx) (default: 3).
-   `--per-payload-max-retries <num>`: Max retries for a payload on network errors (e.g., timeout) (default: 5).

### Network
-   `--method <method>`: HTTP method (default: POST).
-   `--json-body`: Send parameters as a JSON body instead of form data.
-   `--proxy-url <url>`: Route traffic through a proxy like Burp Suite (`http://127.0.0.1:8080`).
-   `--insecure`: Skip SSL certificate verification.
-   `--timeout <seconds>`: Request timeout in seconds (default: 10).

### Output
-   `-v, --verbose`: Show detailed output for all attempts.
-   `--output <file>`: Save successful results to a file in JSON lines format.
-   `--stop-on-success`: Stop the attack after the first success.

---

## Examples

### 1. Basic Login Brute-Force
Try a list of passwords for a single user.
```bash
python run.py https://example.com/login \
  --param username="admin" \
  --param password=passwords.txt \
  --text "Invalid credentials"
```

### 2. Zipping Usernames and Passwords
Try `user1` with `pass1`, `user2` with `pass2`, and so on.
```bash
python run.py https://example.com/login \
  --param username=users.txt \
  --param password=passes.txt \
  --zip-fields "username,password" \
  --text "Invalid credentials"
```

### 3. Combined Zip and Product Attack
Zip a username and password, and for each pair, try a list of MFA tokens.
```bash
python run.py https://example.com/login-mfa \
  --param username=users.txt \
  --param password=passes.txt \
  --param mfa_token=tokens.txt \
  --zip-fields "username,password" \
  --product-fields "mfa_token" \
  --code 200
```

### 4. Brute-Forcing a Header API Key
Test a list of API keys sent in an HTTP header.
```bash
python run.py https://api.example.com/v1/user \
  --method GET \
  --param header:X-Api-Key=keys.txt \
  --code 200
```

### 5. Re-authentication and Saving Output
Generate 6-digit codes and re-authenticate every 100 failures. Save successful codes to a file.
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

## Features

### Basic Usage
- **Targeted Brute-Forcing**: Specify fields to brute-force, such as usernames, passwords, headers, or cookies, using `--param` or `--cookie`.
- **Flexible Payloads**: Supply payloads from files or generate them dynamically during the attack.
- **Custom HTTP Methods**: Select the desired HTTP method (e.g., `GET`, `POST`, `PUT`, `DELETE`, `PATCH`) with the `--method` flag.

### Payload Management
- **File-Based Payloads**: Load payloads from a text file, with each line representing a single payload (e.g., `usernames.txt`).
- **Generated Payloads**: Create combinations on-the-fly using the `generate:chars:length` syntax. For example:
  - `generate:abc:3` produces all 3-character combinations of 'a', 'b', and 'c' (e.g., `aaa`, `aab`, `aba`).
- **Combination Modes**:
  - **Product Mode** (default): Generates the Cartesian product of payloads, testing every possible combination across multiple sources.
  - **Zip Mode**: Pairs payloads from each source in parallel (e.g., username1 with password1), stopping when the shortest list is exhausted.

### Constant and Incrementing Fields
- **Constant Fields**: Set fixed values for fields that remain static during the attack (e.g., `--param api_key=xyz123`).
- **Incrementing Fields**: Automatically increment values with each attempt (e.g., `--param increment:header:X-Request-ID`), perfect for testing counters, CSRF tokens, or request IDs.
- **Cookie Support**: 
  - Static cookies: Define fixed values (e.g., `--cookie session=abc123`).
  - Brute-force cookies: Use payload files (e.g., `--cookie stay-logged-in=cookies.txt`). Cookies are sent in plain text in the `Cookie` header, without URL encoding.

### Authentication Handling
- **Re-Authentication**: Automatically re-authenticate after a set number of failed attempts to maintain a valid session, configured with `--reauth`.
- **Configuration**: Specify a login URL, username, and password (e.g., `--login-url`, `--username`, `--password`) to enable session cookie updates during testing.

### Success Criteria
Define success using one or more conditions:
- **Text Presence**: Check for specific text in the response (e.g., `--expect-text "Welcome"`).
- **Text Absence**: Ensure certain text is absent (e.g., `--no-text "Unauthorized"`).
- **HTTP Status Code**: Match a specific code (e.g., `--code 200`).
# Brute Buddy

Brute Buddy is a versatile tool for security researchers and penetration testers to assess the strength of web applications against brute-force attacks. It supports multi-field brute-forcing, dynamic payload generation, re-authentication, and customizable success criteria for testing forms, headers, cookies, and more.

---

## Features

- Targeted brute-forcing of fields using `--param` and cookies via `--cookie`.
- Flexible payloads: file-based or generated on-the-fly with `generate:chars:length`.
- Combination modes: Cartesian product (default) and zip pairing with `--zip-fields`.
- Constant and incrementing fields (e.g., `--param increment:header:X-Request-ID`).
- Re-authentication support with `--reauth` and `--login-url/--username/--password`.
- Success criteria by regex, expected text, absence of text, status code, response length, or time.
- Multi-threading, retries, proxy support, JSON body requests, optional output file, early stop.

---

## Installation

1. Ensure Python 3.10+ is installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Show help:
   ```bash
   python run.py --help
   ```

See `USAGE.md` for a full feature guide with more examples.

---

## Command-line options (summary)

- Required:
  - `url`: Target URL.
- Parameters and cookies:
  - `--param key=source` where source is `file.txt`, `generate:chars:length`, or a constant value (quoted or unquoted).
  - `--cookie name=source` same sources as above; use `cookie:` or `header:` prefixes inside `--param` to set cookies/headers.
- Combination:
  - `--zip-fields FIELD [FIELD ...]` pair fields by index.
  - `--product-fields FIELD [FIELD ...]` Cartesian product for listed fields (default for all if unspecified).
  - `--max-attempts N` limit total attempts (0 = unlimited).
- Authentication:
  - `--login-url`, `--username`, `--password`, optional `--auth-header KEY=VAL` (repeatable), `--auth-cookie-name NAME`, `--reauth N`.
- Success criteria:
  - `--regex PATTERN`, `--expect-text TEXT`, `--text TEXT`, `--code INT`, `--length INT`, `--time SEC`.
- Performance/network:
  - `--threads N` (default 5), `--delay SEC` (default 0.1), `--retries N` (default 3).
  - `--method METHOD`, `--timeout SEC`, `--proxy-url URL`, `--insecure`, `--json-body`.
  - Retries: by default, each payload is retried on network errors until an HTTP response is received; disable with `--no-retry-until-response`. Control adapter retries with `--retries` and `--retry-backoff`.
- Output:
  - `-v/--verbose`, `--output FILE` (JSON lines), `--stop-on-success`.

---

## Examples

1) Basic username/password brute-force
```bash
python run.py https://example.com/login \
  --param username=usernames.txt \
  --param password=passwords.txt \
  --expect-text "Welcome" \
  --threads 10
```

2) Generated MFA with re-authentication and incrementing header
```bash
python run.py https://example.com/mfa \
  --param mfa-code=generate:0123456789:6 \
  --param increment:header:X-Request-ID \
  --code 200 \
  --reauth 100 --login-url https://example.com/login \
  --username admin --password pass123
```

3) Cookie + header zip, regex success, via proxy
```bash
python run.py https://example.com/api \
  --cookie stay-logged-in=cookies.txt \
  --param header:X-API-Key=keys.txt \
  --zip-fields cookie:stay-logged-in header:X-API-Key \
  --regex "Success.*" \
  --proxy-url http://127.0.0.1:8080 --insecure
```

4) Zip username/password and product with token
```bash
python run.py https://example.com/auth \
  --param username=users.txt --param password=passes.txt \
  --param token=tokens.txt \
  --zip-fields username password \
  --product-fields token \
  --text "Invalid"
```

5) JSON body request with early stop and output file
```bash
python run.py https://example.com/login \
  --param username=users.txt --param password=passes.txt \
  --json-body --code 200 \
  --stop-on-success --output hits.jsonl
```

---

## Notes

- `--text` indicates failure text; success is when this text is NOT present.
- `--zip-fields` and `--product-fields` accept multiple values separated by spaces or commas and may be repeated.
- In streaming mode, total attempts may be unknown if lists are very large; the tool schedules work efficiently without loading all combinations into memory.

---

## Troubleshooting

- Proxy timeouts (via `--proxy-url`): If the proxy is down/slow, requests will retry with exponential backoff and, by default, the same payload will be re-queued until an HTTP response is received. To prevent long waits, set `--per-payload-max-retries` or disable with `--no-retry-until-response`.
- Network/server down: By default, a payload keeps retrying on network errors until a response. You can cap re-queues with `--per-payload-max-retries` or turn off strict delivery via `--no-retry-until-response`. Adapter-level retries are also controlled by `--retries` and `--retry-backoff`.
- Verbose output: `-v/--verbose` prints per-attempt logs when attempts complete (success or failure). If attempts are slow (timeouts), logs will appear once they finish. In streaming mode, the initial message may show only the first batch scheduled (e.g., 10 with `--threads 10`).
- Streaming scheduler: The tool schedules up to `--threads` attempts initially, then refills as each attempt completes. It does not load all combinations at once, enabling large wordlists.

If issues persist, try a quick control run without a proxy and shorter timeouts to isolate network conditions.

---

## License

MIT
- Performance/network:
