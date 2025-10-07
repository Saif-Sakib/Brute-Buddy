import requests
from time import perf_counter, sleep
import urllib3
import re


def check_success(response, elapsed, args):
    """Check if the response indicates a successful attempt."""
    if response is None:
        return False
    
    # Early return for performance
    response_text = response.text
    
    # Priority order: most specific to least specific
    if args.regex and re.search(args.regex, response_text):
        return True
    
    if args.expect_text and args.expect_text in response_text:
        return True
    
    if args.text and args.text not in response_text:
        return True
    
    if args.code and response.status_code == args.code:
        return True
    
    if args.length and len(response_text) == args.length:
        return True
    
    if args.time and elapsed >= args.time:
        return True
    
    return False


def make_attempt(url, all_values, increment_fields, counter_val, args, auth=None, session=None):
    """Execute a single brute-force attempt."""
    if args.insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Separate parameters by type
    body, headers, cookies = {}, {}, {}
    
    for key, value in all_values.items():
        if key.startswith("header:"):
            headers[key[7:]] = value
        elif key.startswith("cookie:"):
            cookies[key[7:]] = value
        else:
            body[key] = value

    # Add increment fields
    counter_str = str(counter_val)
    for field in increment_fields:
        if field.startswith("header:"):
            headers[field[7:]] = counter_str
        elif field.startswith("cookie:"):
            cookies[field[7:]] = counter_str
        else:
            body[field] = counter_str

    # Prepare request parameters
    proxies = {'http': args.proxy_url, 'https': args.proxy_url} if args.proxy_url else None
    method_lower = args.method.lower()
    
    # Optimize parameter placement based on method and --json-body
    json_body = None
    if method_lower in ["post", "put", "patch"]:
        if args.json_body:
            json_body, data, params = body, None, None
        else:
            data, params = body, None
    else:
        data, params = None, body

    try:
        start_time = perf_counter()
        sess = session or requests.Session()
        response = sess.request(
            method=args.method,
            url=url,
            data=data,
            json=json_body,
            params=params,
            headers=headers,
            cookies=cookies,
            verify=not args.insecure,
            proxies=proxies,
            timeout=args.timeout
        )
        elapsed = perf_counter() - start_time
        
        # Apply delay after timing measurement
        if args.delay > 0:
            sleep(args.delay)
        
        return all_values, counter_val, response, elapsed
        
    except requests.RequestException as e:
        return all_values, counter_val, None, 0, str(e)