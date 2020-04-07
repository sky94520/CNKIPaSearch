import requests
from .config import PROXY_URL


class Proxy(object):
    def __init__(self):
        self._proxy = None
        self.dirty = True

    def get_proxy(self):
        if self.dirty:
            self._proxy = self._get_random_proxy()
            self.dirty = False
        return self._proxy

    def _get_random_proxy(self):
        response = requests.get(PROXY_URL, timeout=2)
        return response.text
