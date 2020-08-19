import requests
from config import PROXY_URL


class GetProxyError(Exception):
    """获取代理失败"""
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


class Proxy(object):
    def __init__(self):
        self._proxy = None
        self.dirty = True

    def get_proxy(self):
        if self.dirty or self._proxy is None:
            self._proxy = self._get_random_proxy()
            if self._proxy:
                self.dirty = False
        return self._proxy

    def _get_random_proxy(self):
        response = requests.get(PROXY_URL, timeout=2)
        # 服务器访问失败
        if response.status_code != 200:
            return None
        json_data = response.json()
        if 'success' not in json_data or json_data['success'] != 'true':
            raise GetProxyError(json_data)
        data = json_data['data'][0]
        return data['IP']
