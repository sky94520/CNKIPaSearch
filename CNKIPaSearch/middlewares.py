# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import os
import time
import logging
import requests
from scrapy.http import HtmlResponse
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from .hownet_config import *
from .Proxy import Proxy


logger = logging.getLogger(__name__)
# 代理
PROXY = Proxy()


class GetFromLocalityMiddleware(object):
    def process_request(self, request, spider):
        """
        尝试从本地获取源文件，如果存在，则直接获取
        :param request:
        :param spider:
        :return:
        """
        # 提取出code
        filename = request.meta['publication_number']
        # 文件存放位置
        path = request.meta['path']
        # 该路径存在该文件
        filepath = os.path.join(path, '%s.html' % filename)
        if os.path.exists(filepath):
            fp = open(filepath, 'rb')
            body = fp.read()
            fp.close()
            # 从本地加载的文件不再重新写入
            request.meta['load_from_local'] = True
            return HtmlResponse(url=request.url, headers=request.headers, body=body, request=request)
        return None


class RetryOrErrorMiddleware(RetryMiddleware):
    """在官方的基础上增加了一条判断语句，当重试次数超过阈值时，发出错误"""

    def _retry(self, request, reason, spider):
        # 获取当前的重试次数
        retry_times = request.meta.get('retry_times', 0) + 1
        # 最大重试次数
        max_retry_times = self.max_retry_times
        if 'max_retry_times' in request.meta:
            max_retry_times = request.meta['max_retry_times']

        PROXY.dirty = True
        # 超出重试次数，记录
        if retry_times >= max_retry_times:
            spider.request_error()
            # logger.error('%s %s retry times beyond the bounds' % (request.url, datum))
            logger.error('%s retry times beyond the bounds' % request.url)
        # super()._retry(request, reason, spider)

    def process_exception(self, request, exception, spider):
        # 出现错误，再次请求
        logger.warning(exception)
        PROXY.dirty = True
        return request


class ProxyMiddleware(object):
    def process_request(self, request, spider):
        # 最大重试次数
        retry_times = request.meta.get('retry_times', 0)
        max_retry_times = spider.crawler.settings.get('MAX_RETRY_TIMES')
        # 代理更新失败，则重新请求
        proxy = PROXY.get_proxy()
        if proxy is None:
            return request
        # 最后一次尝试不使用代理
        if proxy and retry_times != max_retry_times:
            logger.info('使用代理%s' % proxy)
            request.meta['proxy'] = 'http://%s' % proxy
        else:
            reason = '代理获取失败' if proxy is None else ('达到最大重试次数[%d/%d]' % (retry_times, max_retry_times))
            logger.warning('%s，使用自己的IP' % reason)


class CookieMiddleware(object):
    def __init__(self):
        # 使用那个类作为配置文件
        self.config = BaseConfig

    def process_request(self, request, spider):
        # 重新请求cookie
        cookie = None
        if spider.cookie_dirty and not spider.request_queue_empty:
            # 死循环获取cookie
            global PROXY
            while not cookie:
                proxy = PROXY.get_proxy()
                proxies = {'http': proxy}
                # 根据条件获取cookie
                cookie = self.get_cookie(spider.request_datum, proxies)
                logger.warning('获取cookie %s' % cookie)
                # cookie获取失败，更换代理重新获取
                if cookie is None or len(cookie) == 0:
                    PROXY.dirty = True
                    time.sleep(1)
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
        # 动态获取配置类
        params = BaseConfig.get_config_params(values)
        params.update(**kwargs)
        url = 'http://kns.cnki.net/kns/request/SearchHandler.ashx'
        try:
            response = requests.post(url, params=params, proxies=proxies, timeout=5)
            cookies = requests.utils.dict_from_cookiejar(response.cookies)

            cookie_str = ""
            for key in cookies:
                value = cookies[key]
                text = "%s=%s;" % (key, value)
                cookie_str += text
            return cookie_str
        except Exception as e:
            logger.warning('cookie获取失败')
        return None

