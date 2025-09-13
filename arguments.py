import argparse


def parse_arguments():
    """Parse and return command-line arguments."""
    parser = argparse.ArgumentParser(
        description="A user-friendly brute-force tool with re-authentication support.",
        epilog="Run 'python run.py --help' for detailed usage and examples.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Required arguments
    parser.add_argument("url", help="Target URL to brute-force (e.g., https://example.com/login)")
    
    # Parameter specifications
    parser.add_argument("--param", action="append",
                        help="Parameter specification: key=source (e.g., username=user.txt, password=\"secret\", header:X-API-Key=keys.txt, increment:counter)")
    parser.add_argument("--cookie", action="append",
                        help="Cookie specification: name=source (e.g., session=cookies.txt)")
    
    # Combination strategies
    parser.add_argument("--zip-fields", action="append",
                        help="Fields to combine with zip (e.g., username, password)")
    parser.add_argument("--product-fields", action="append",
                        help="Fields to combine with product (e.g., username, password)")
    
    # Authentication
    parser.add_argument("--login-url", help="URL for re-authentication")
    parser.add_argument("--username", help="Username for re-authentication")
    parser.add_argument("--password", help="Password for re-authentication")
    parser.add_argument("--auth-header", action="append",
                        help="Custom header for authentication (e.g., X-API-Key=value)")
    parser.add_argument("--reauth", type=int, default=0,
                        help="Re-authenticate after this many failures (0 = disabled)")
    
    # Success criteria
    parser.add_argument("--text", help="Text indicating failure (not present = success)")
    parser.add_argument("--expect-text", help="Text indicating success (present = success)")
    parser.add_argument("--regex", help="Regex pattern indicating success (match = success)")
    parser.add_argument("--code", type=int, help="Success HTTP status code")
    parser.add_argument("--length", type=int, help="Success response length")
    parser.add_argument("--time", type=float, help="Minimum response time for success")
    
    # Performance settings
    parser.add_argument("--threads", type=int, default=5, help="Number of threads (default: 5)")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between requests (default: 0.1s)")
    parser.add_argument("--retries", type=int, default=3, help="Retries for failed requests (default: 3)")
    
    # Network settings
    parser.add_argument("--proxy-url", help="Proxy URL (e.g., http://127.0.0.1:8080)")
    parser.add_argument("--insecure", action="store_true", help="Skip SSL verification")
    parser.add_argument("--method", default="POST", help="HTTP request method (e.g., GET, POST, PUT, DELETE, PATCH)")
    parser.add_argument("--timeout", type=float, default=20, help="Request timeout in seconds (default: 20)")
    
    # Output settings
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")
    
    return parser.parse_args()