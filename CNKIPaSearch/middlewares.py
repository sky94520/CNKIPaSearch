# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import os
import random
import logging
import requests
from scrapy.http import HtmlResponse, TextResponse
from scrapy.exceptions import IgnoreRequest
from scrapy.downloadermiddlewares.retry import RetryMiddleware

from .hownet_config import *
from .Proxy import Proxy, GetProxyError
from .spiders.page import PageSpider
from .pipelines import get_path


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
        # 提取文件路径和名称
        if isinstance(spider, PageSpider):
            index = spider.cur_page
            html_full_path = os.path.join(get_path(spider, 'html'), '%s.html' % index)
            json_full_path = os.path.join(get_path(spider, 'json'), '%s.json' % index)
        else:
            filename = request.meta['publication_number']
            prefix_path = request.meta['prefix_path']
            html_full_path = os.path.join(spider.basedir, 'html', prefix_path, '%s.html' % filename)
            json_full_path = os.path.join(spider.basedir, 'json', prefix_path, '%s.json' % filename)
        # 同时存在，则不再处理该request
        if os.path.exists(html_full_path) and os.path.exists(json_full_path):
            raise IgnoreRequest('json file has exists.')
        if os.path.exists(html_full_path):
            fp = open(html_full_path, 'rb')
            body = fp.read()
            fp.close()
            # 从本地加载的文件不再重新写入
            request.meta['load_from_local'] = True
            return HtmlResponse(url=request.url, headers=request.headers, body=body, request=request)
        return None


class LoadJsonFromLocalityMiddleware(object):
    """从本地加载json文件"""
    def process_request(self, request, spider):
        """
        尝试从本地获取源文件，如果存在，则直接获取
        :param request:
        :param spider:
        :return:
        """
        filename = request.meta['publication_number']
        path = request.meta['path']
        full_filename = os.path.join(path, '%s.json' % filename)
        # 从本地读取文件
        if os.path.exists(full_filename):
            fp = open(full_filename, 'rb')
            body = fp.read()
            fp.close()
            # 从本地加载的文件不再重新写入
            request.meta['load_from_local'] = True
            return TextResponse(url=request.url, headers=request.headers, body=body, request=request)
        return IgnoreRequest('not found the file:%s' % full_filename)


class RetryOrErrorMiddleware(RetryMiddleware):
    """在官方的基础上增加了一条判断语句，当重试次数超过阈值时，发出错误"""

    def _retry(self, request, reason, spider):
        # 获取当前的重试次数
        return self._process(request, spider)

    def process_exception(self, request, exception, spider):
        if isinstance(exception, IgnoreRequest):
            return
        if isinstance(exception, TimeoutError):
            return self._process(request, spider)
        # 代理获取失败，一秒后再访问
        logger.warning(exception)
        # TODO:不起作用 原因见README
        if isinstance(exception, GetProxyError):
            pass
        # 出现错误，再次请求
        PROXY.dirty = True
        return request

    def _process(self, request, spider):
        """
        处理请求，如果超过最大次数，则在数据队列中删除这个请求，并且会抛出IgnoreRequest异常
        :param request:
        :param spider:
        :return:
        """
        retry_times = request.meta.get('retry_times', 0) + 1
        request.meta['retry_times'] = retry_times
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
            return IgnoreRequest()
        else:
            return request
        # super()._retry(request, reason, spider)


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
        # TODO:
        self.user_agents = UserAgentMiddleware()

    def process_request(self, request, spider):
        # 重新请求cookie
        cookie = None
        if spider.cookie_dirty and not spider.request_queue_empty:
            # 死循环获取cookie
            global PROXY
            while not cookie:
                proxy = PROXY.get_proxy()
                proxies = {'http': proxy, 'https': proxy}
                logger.info('使用代理%s' % proxy)
                # 根据条件获取cookie
                cookie = self.get_cookie(spider.request_datum, proxies)
                logger.warning('获取cookie %s' % cookie)
                # cookie获取失败，更换代理重新获取
                if cookie is None or len(cookie) == 0:
                    PROXY.dirty = True
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
        # url = 'http://kns.cnki.net/kns/request/SearchHandler.ashx'
        url = 'http://nvsm.cnki.net/kns/request/SearchHandler.ashx'
        try:
            # user_agent = self.user_agents.get_random_user_agent()
            response = requests.post(url, params=params, proxies=proxies, timeout=5)
            cookies = requests.utils.dict_from_cookiejar(response.cookies)

            cookie_str = ""
            for key in cookies:
                value = cookies[key]
                text = "%s=%s;" % (key, value)
                cookie_str += text
            return cookie_str
        except Exception as e:
            # logger.warning('cookie获取失败')
            logger.warning(e)
        return None


class UserAgentMiddleware(object):
    def __init__(self):
        self.user_agents = [
            """Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 
            Safari/537.36""",
            """Mozilla/5.0 (Windows NT 6.2; WOW64; rv:21.0) Gecko/20100101 Firefox/21.0""",
            """User-Agent:Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, 
            like Gecko)Ubuntu/11.10 Chromium/27.0.1453.93 Chrome/27.0.1453.93 Safari/537.36""",
            """User-Agent:Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/533.20.25 (KHTML, 
            like Gecko) Version/5.0.4 Safari/533.20.27""",
            """User-Agent:Opera/9.80 (Windows NT 6.1; WOW64; U; en) Presto/2.10.229 Version/11.62""",
            """User-Agent:Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.9.168 Version/11.52"""
        ]

    def process_request(self, request, spider):
        request.headers['User-Agent'] = self.get_random_user_agent()

    def get_random_user_agent(self):
        return random.choice(self.user_agents)