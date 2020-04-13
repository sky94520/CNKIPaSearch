import logging
import requests
from .config import PROXY_URL


class Proxy(object):
    def __init__(self):
        self._proxy = None
        self.dirty = True

    def get_proxy(self):
        if self.dirty or self._proxy is None:
            self._proxy = self._get_random_proxy()
            self.dirty = False
        return self._proxy

    def _get_random_proxy(self):
        try:
            response = requests.get(PROXY_URL, timeout=2)
            if response.status_code != 200:
                return None
            json_data = response.json()
            if 'success' not in json_data or json_data['success'] != 'true':
                return None
            data = json_data['data'][0]
            return data['IP']
        except Exception as e:
            logging.warning(e)
