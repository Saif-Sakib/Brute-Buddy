import requests
from time import perf_counter, sleep
import urllib3
import re

# Disable warnings for insecure requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_success(response, elapsed, args):
    """Check if the response indicates a successful attempt based on user-defined criteria."""
    if response is None:
        return False

    response_text = response.text

    # A list of conditions to check. The first one to be true determines success.
    conditions = [
        (args.regex and re.search(args.regex, response_text)),
        (args.expect_text and args.expect_text in response_text),
        (args.text and args.text not in response_text),
        (args.code and response.status_code == args.code),
        (args.length and len(response_text) == args.length),
        (args.time and elapsed >= args.time),
    ]

    return any(conditions)


def make_attempt(url, payload, increment_value, args, session):
    """Executes a single brute-force attempt."""
    
    headers = {}
    cookies = {}
    body_params = {}

    # Distribute payload values into headers, cookies, and body
    for key, value in payload.items():
        if key.startswith("header:"):
            headers[key[7:]] = value
        elif key.startswith("cookie:"):
            cookies[key[7:]] = value
        else:
            body_params[key] = value

    # Handle incrementing fields
    if increment_value is not None:
        counter_str = str(increment_value)
        for field in args.increment_fields:
            if field.startswith("header:"):
                headers[field[7:]] = counter_str
            elif field.startswith("cookie:"):
                cookies[field[7:]] = counter_str
            else:
                body_params[field] = counter_str

    # Prepare request arguments
    request_args = {
        "method": args.method,
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": args.timeout,
        "verify": not args.insecure,
    }

    if args.proxy_url:
        request_args["proxies"] = {'http': args.proxy_url, 'https': args.proxy_url}

    # Handle body/params based on HTTP method
    if args.method.upper() in ["POST", "PUT", "PATCH"]:
        if args.json_body:
            request_args["json"] = body_params
        else:
            request_args["data"] = body_params
    else:
        request_args["params"] = body_params

    try:
        start_time = perf_counter()
        response = session.request(**request_args)
        elapsed = perf_counter() - start_time

        if args.delay > 0:
            sleep(args.delay)

        return payload, increment_value, response, elapsed

    except requests.RequestException as e:
        return payload, increment_value, None, 0, str(e)