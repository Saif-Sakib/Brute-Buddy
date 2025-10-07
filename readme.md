# Brute Buddy

The **Brute Buddy** is a versatile and robust tool crafted for security researchers and penetration testers to assess the strength of web applications against brute-force attacks. With support for multi-field brute-forcing, dynamic payload generation, re-authentication, and highly customizable success criteria, it’s an ideal choice for testing authentication endpoints, headers, cookies, and more.

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

## License

MIT
- Performance/network:
