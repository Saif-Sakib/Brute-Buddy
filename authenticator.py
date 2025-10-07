import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class Authenticator:
    """Manage authentication and re-authentication."""
    
    def __init__(self, login_url, username, password, proxy_url=None, insecure=False, headers=None, cookie_name="session"):
        self.login_url = login_url
        self.username = username
        self.password = password
        self.proxy_url = proxy_url
        self.insecure = insecure
        self.headers = headers or {}
        self.cookie_name = cookie_name or "session"
        
        # Setup session with optimized retry strategy
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods={"POST", "GET"}
        )
        adapter = HTTPAdapter(max_retries=retries, pool_connections=1, pool_maxsize=1)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.proxies = {'http': proxy_url, 'https': proxy_url} if proxy_url else None

    def authenticate(self):
        """Authenticate and return the session cookie value (by name)."""
        try:
            response = self.session.post(
                self.login_url,
                data={'username': self.username, 'password': self.password},
                headers=self.headers,
                verify=not self.insecure,
                proxies=self.proxies,
                timeout=20
            )
            response.raise_for_status()
            
            cookies = response.cookies.get_dict()
            if self.cookie_name not in cookies:
                raise ValueError(f"No '{self.cookie_name}' cookie received")
            
            return cookies[self.cookie_name]
            
        except requests.RequestException as e:
            raise Exception(f"Authentication error: {e}")

    def close(self):
        """Close the HTTP session."""
        if hasattr(self, 'session'):
            self.session.close()