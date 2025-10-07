# Brute Buddy Usage Guide

This guide explains every feature with examples.

## Parameters and Cookies

- Brute-force from files or generated payloads:
  - `--param username=users.txt`
  - `--param password=generate:0123456789:6`
- Constants (quoted or unquoted):
  - `--param role="admin"`
- Headers and cookies via prefix:
  - `--param header:X-API-Key=keys.txt`
  - `--cookie session=sessions.txt`

## Combination Strategies

- Zip specific fields together:
  - `--zip-fields username password`
- Product specific fields:
  - `--product-fields token`
- If neither is provided, all brute-force fields are in product mode by default.
- You can pass multiple values separated by spaces or commas, and repeat the flag.

## Increment Fields

- Add incrementing counters per attempt (to body, header, or cookie):
  - `--param increment:request-id`
  - `--param increment:header:X-Request-ID`
  - `--param increment:cookie:visit`

## Authentication and Re-auth

- Re-authenticate after N consecutive failures:
  - `--reauth 100 --login-url https://example.com/login --username user --password pass`
- Add custom authentication headers:
  - `--auth-header X-Device-ID=abc --auth-header X-App=web`
- Use a different cookie name from login response:
  - `--auth-cookie-name auth_token`

## Success Criteria

- Regex success: `--regex "Welcome, .*"`
- Expected text present: `--expect-text "Dashboard"`
- Failure text absent: `--text "Invalid"`
- Status code match: `--code 200`
- Exact length: `--length 5120`
- Slow response: `--time 2.5`

Use any combination; the first match counts as success.

## Performance and Networking

- Threads & pacing: `--threads 20 --delay 0.1 --retries 3`
- Method & timeout: `--method POST --timeout 20`
- Proxy and TLS: `--proxy-url http://127.0.0.1:8080 --insecure`

## JSON Body

- Send JSON instead of form data for write methods:
  - `--json-body`

## Output and Control

- Verbose logging: `-v` or `--verbose`
- Save successes to file: `--output hits.jsonl`
- Stop at first success: `--stop-on-success`
- Limit attempts: `--max-attempts 1000`

## Examples

1) Basic username/password with product
```bash
python run.py https://example.com/login \
  --param username=users.txt \
  --param password=passes.txt \
  --expect-text "Welcome" \
  --threads 10
```

2) Zip username/password pairs and product with token
```bash
python run.py https://example.com/auth \
  --param username=users.txt --param password=passes.txt \
  --param token=tokens.txt \
  --zip-fields username password \
  --product-fields token \
  --regex "^OK$"
```

3) Cookie + header brute-force with proxy
```bash
python run.py https://example.com/api \
  --cookie stay-logged-in=cookies.txt \
  --param header:X-API-Key=keys.txt \
  --zip-fields cookie:stay-logged-in header:X-API-Key \
  --code 200 \
  --proxy-url http://127.0.0.1:8080 --insecure
```

4) MFA code generation with incrementing header and reauth
```bash
python run.py https://example.com/mfa \
  --param mfa-code=generate:0123456789:6 \
  --param increment:header:X-Request-ID \
  --code 200 \
  --reauth 100 --login-url https://example.com/login \
  --username admin --password pass123 \
  --auth-header X-Device-ID=abc \
  --auth-cookie-name auth_token
```

5) JSON body login with early stop, output file
```bash
python run.py https://example.com/login \
  --param username=users.txt --param password=passes.txt \
  --json-body --code 200 \
  --stop-on-success --output hits.jsonl
```