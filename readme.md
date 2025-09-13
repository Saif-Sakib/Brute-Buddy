Below is an updated and comprehensive `README.md` for the **Ultimate Brute Forcer**, based on the provided draft and expanded with additional details for clarity, functionality, and usability. This version enhances the original structure, refines descriptions, and adds practical examples and tips.

---

# Ultimate Brute Forcer

The **Ultimate Brute Forcer** is a versatile and robust tool crafted for security researchers and penetration testers to assess the strength of web applications against brute-force attacks. With support for multi-field brute-forcing, dynamic payload generation, re-authentication, and highly customizable success criteria, it’s an ideal choice for testing authentication endpoints, headers, cookies, and more.

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
- **Response Length**: Verify an exact response body length (e.g., `--length 500`).
- **Response Time**: Flag success if the response time exceeds a threshold (e.g., `--time 2.0` for 2 seconds).

### Advanced Options
- **Multi-Threading**: Control concurrency with `--threads` to optimize speed without overwhelming the target.
- **Request Delay**: Add a delay between requests (e.g., `--delay 0.5` for 0.5 seconds) to evade detection or rate limits.
- **Retries**: Retry failed requests up to a specified limit (e.g., `--retries 3`).
- **Proxy Support**: Route traffic through a proxy (e.g., `--proxy http://localhost:8080`) for monitoring or bypassing restrictions.
- **SSL Verification**: Disable SSL certificate checks with `--no-verify` (warnings suppressed for cleaner output).
- **Verbose Mode**: Enable detailed logging with `--verbose` to track each attempt’s request and response.

---

## Installation

To set up the **Ultimate Brute Forcer**, follow these steps:

1. **Clone or Download the Repository**:
   - Clone using Git:
     ```bash
     git clone https://github.com/yourusername/ultimate-brute-forcer.git
     ```
   - Or download the ZIP file and extract it.

2. **Install Dependencies**:
   - Ensure Python 3.x is installed.
   - Install required libraries:
     ```bash
     pip install requests urllib3
     ```

3. **Run the Tool**:
   - Navigate to the project directory and check available options:
     ```bash
     python run.py --help
     ```

---

## Usage Examples

Below are practical examples to demonstrate the tool’s capabilities:

### Example 1: Basic Username and Password Brute-Force
```bash
python run.py https://example.com/login \
  --param username=usernames.txt \
  --param password=passwords.txt \
  --expect-text "Welcome" \
  --threads 10
```
- Brute-forces usernames and passwords from files.
- Looks for "Welcome" in the response to identify success.
- Uses 10 concurrent threads.

### Example 2: Generated Payloads with Re-Authentication
```bash
python run.py https://example.com/mfa \
  --param mfa-code=generate:0123456789:6 \
  --param increment:header:X-Request-ID \
  --code 200 \
  --reauth 100 \
  --login-url https://example.com/login \
  --username admin \
  --password pass123
```
- Generates 6-digit MFA codes using digits 0-9.
- Adds an incrementing `X-Request-ID` header.
- Expects a 200 status code.
- Re-authenticates every 100 failed attempts.

### Example 3: Cookie and Header Brute-Force with Zip Mode
```bash
python run.py https://example.com/api \
  --cookie stay-logged-in=cookies.txt \
  --param header:X-API-Key=keys.txt \
  --zip-fields cookie:stay-logged-in header:X-API-Key \
  --regex "Success.*"
```
- Brute-forces the `stay-logged-in` cookie and `X-API-Key` header.
- Uses zip mode to pair cookie and header values.
- Checks for a regex match of "Success.*".

### Example 4: Combining Zip and Product Modes
```bash
python run.py https://example.com/auth \
  --param username=users.txt \
  --param password=passes.txt \
  --param token=tokens.txt \
  --zip-fields username password \
  --product-fields token \
  --no-text "Invalid"
```
- Zips `username` and `password` (e.g., username1 with password1).
- Combines zipped pairs with each `token` using product mode.
- Succeeds if "Invalid" is absent in the response.

---

## Tips

- **Performance Tuning**: Start with fewer threads (e.g., 5-10) and adjust based on server response times.
- **Payload Optimization**: Use generated payloads for small character sets to manage memory usage.
- **Combination Modes**: Choose zip mode for synchronized fields (e.g., username/password pairs) and product mode for independent fields.
- **Re-Authentication**: Enable for endpoints requiring active sessions, especially with multi-threading.
- **Proxy Usage**: Pair with tools like Burp Suite for request inspection.
- **Verbose Mode**: Use for debugging or detailed analysis of request/response flows.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
