import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class Authenticator:
    """Manages authentication and re-authentication."""

    def __init__(self, login_url, username, password, proxy_url=None, insecure=False, headers=None, cookie_name="session"):
        self.login_url = login_url
        self.username = username
        self.password = password
        self.proxy_url = proxy_url
        self.insecure = insecure
        self.headers = headers or {}
        self.cookie_name = cookie_name or "session"
        self.session = self._create_session()

    def _create_session(self):
        """Creates a requests session with a retry mechanism."""
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.2,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        if self.proxy_url:
            session.proxies = {'http': self.proxy_url, 'https': self.proxy_url}
        
        session.verify = not self.insecure

        return session

    def authenticate(self):
        """Authenticates and returns the session cookie value."""
        try:
            response = self.session.post(
                self.login_url,
                data={'username': self.username, 'password': self.password},
                headers=self.headers,
                timeout=20
            )
            response.raise_for_status()

            cookies = response.cookies.get_dict()
            if self.cookie_name not in cookies:
                raise ValueError(f"Authentication successful, but cookie '{self.cookie_name}' not found in response.")

            return cookies[self.cookie_name]

        except requests.RequestException as e:
            raise Exception(f"Authentication failed: {e}")

    def close(self):
        """Closes the HTTP session."""
        self.session.close()