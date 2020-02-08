# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import os
import json
import logging
import requests
from twisted.internet.error import TimeoutError
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from .hownet_config import *


logger = logging.getLogger(__name__)


def get_random_proxy():
    """获取随机的IP地址"""
    url = 'http://47.107.246.172:5555/random'
    response = requests.get(url, timeout=10)
    datum = json.loads(response.text)
    if datum['status'] == 'success':
        return datum['proxy']
    else:
        logger.error(datum['msg'])
        return None


def date2str(date):
    date_string = date.strftime('%Y-%m-%d')
    return date_string


class RetryOrErrorMiddleware(RetryMiddleware):
    """在之前的基础上增加了一条判断语句，当重试次数超过阈值时，发出错误"""

    def _retry(self, request, reason, spider):
        # 获取当前的重试次数
        retry_times = request.meta.get('retry_times', 0) + 1
        # 最大重试次数
        max_retry_times = self.max_retry_times
        if 'max_retry_times' in request.meta:
            max_retry_times = request.meta['max_retry_times']

        # 超出重试次数
        if retry_times > max_retry_times:
            datum = spider.request_error()
            logger.error('%s %s retry times beyond the bounds' % (request.url, datum))
        super()._retry(request, reason, spider)

    def process_exception(self, request, exception, spider):
        # 出现超时错误时，再次请求
        if isinstance(exception, TimeoutError):
            return requests


class ProxyMiddleware(object):

    def process_request(self, request, spider):
        # 最大重试次数
        retry_times = request.meta.get('retry_times', 0)
        max_retry_times = spider.crawler.settings.get('MAX_RETRY_TIMES')
        proxy = get_random_proxy()
        # 最后一次尝试不使用代理
        if proxy and retry_times != max_retry_times:
            logger.info('使用代理%s' % proxy)
            request.meta['proxy'] = 'http://%s' % proxy
        else:
            reason = '代理获取失败' if proxy else ('达到最大重试次数[%d/%d]' % (retry_times, max_retry_times))
            logger.warning('%s，使用自己的IP' % reason)


class CookieMiddleware(object):

    def __init__(self):
        # 使用那个类作为配置文件
        name = os.getenv('config', 'ApplicantConfig')
        self.config = configurations[name]

    def process_request(self, request, spider):
        # 重新请求cookie
        if spider.cookie_dirty:
            # 死循环获取cookie
            cookie = None
            while not cookie:
                proxy = get_random_proxy()
                proxies = {'http': proxy}
                # 根据条件获取cookie
                cookie = self.get_cookie(spider.request_datum, proxies)
                logger.warning('获取cookie %s' % cookie)
            spider.cookie = cookie
        # 赋值cookie
        request.headers['Cookie'] = spider.cookie

    def get_cookie(self, values, proxies=None, **kwargs):
        """
        根据条件给知网发送post请求来获取对应的cookie
        :param values: dict类型的变量
        :param proxies: 代理 proxies = {'http': 'host:port', 'https': 'host:port'}
        :return: cookie 字符串类型，主要用于赋值到header中的Cookie键
        headers = {'Cookie': cookie}
        """
        params = self.config.get_params(**values)
        params.update(**kwargs)
        url = 'http://kns.cnki.net/kns/request/SearchHandler.ashx'
        try:
            response = requests.post(url, params=params, proxies=proxies)
            cookies = requests.utils.dict_from_cookiejar(response.cookies)

            cookie_str = ""
            for key in cookies:
                value = cookies[key]
                text = "%s=%s;" % (key, value)
                cookie_str += text
            return cookie_str
        except Exception as e:
            print(e)
        return None

