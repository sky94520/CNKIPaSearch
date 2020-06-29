# -*- coding: utf-8 -*-
"""
专门用于爬取申请人-专利数量
"""
import re
import scrapy
from urllib.parse import urlencode
from . import IdentifyingCodeError
from ..items import NumberItem
from CNKIPaSearch.params.PagePersistParam import PagePersistParam


class NumberSpider(scrapy.Spider):
    name = 'number'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'CNKIPaSearch.middlewares.RetryOrErrorMiddleware': 550,
            'CNKIPaSearch.middlewares.ProxyMiddleware': 843,
            'CNKIPaSearch.middlewares.CookieMiddleware': 844,
        },
        'ITEM_PIPELINES': {
            'CNKIPaSearch.pipelines.SaveNumberCsvPipeline': 300,
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pattern = r'\d+(\,\d+)*'
        # 是否请求新的cookie
        self._cookie_dirty, self._cookie = True, None
        self.params = None

    def start_requests(self):
        """
        scrapy会调用该函数获取Request
        :return:
        """
        page_dir = self.settings.get('PAGE_DIR')
        self.logger.info('the file path is %s', page_dir)
        self.params = PagePersistParam(page_dir)
        # 获取链接的位置
        request = self._create_request(self.params.cur_page)
        self.logger.info('开始爬取')
        if request:
            yield request

    def parse(self, response):
        """
        从页面提取数据并进行处理
        :param response:
        :return:
        """
        self.logger.info('正在爬取')
        # 解析页面，如果出现验证码则重新请求
        try:
            item = self._parse_html(response)
        except IdentifyingCodeError as e:
            self.logger.error(e)
            self._cookie_dirty = True
            yield self._create_request(self.params.cur_page)
            return
        # 返回items
        yield item
        # 开始新的一个
        self._cookie_dirty = True
        self.params.request_success()
        # 回写checkpoint
        self.params.save()
        if len(self.params.request_queue) == 0:
            return None
        yield self._create_request(self.params.cur_page)

    def _create_request(self, cur_page):
        """
        创建一个专利页面的请求
        :param cur_page: 要获取的页面
        :return: request 返回请求
        """
        params = {
            'ID': '',
            'tpagemode': 'L',
            'dbPrefix': 'SCPD',
            'Fields': '',
            'DisplayMode': 'listmode',
            'PageName': 'ASP.brief_result_aspx',
            'isinEn': 0,
            'QueryID': 3,
            'sKuaKuID': 3,
            'turnpage': 1,
            'RecordsPerPage': self.settings.get('PATENT_NUMBER_PER_PAGE', 50),
            'curpage': cur_page,
        }
        base_url = 'http://kns.cnki.net/KNS/brief/brief.aspx'
        url = '%s?%s' % (base_url, urlencode(params))
        meta = {
            'max_retry_times': self.crawler.settings.get('MAX_RETRY_TIMES')
        }
        return scrapy.Request(url=url, callback=self.parse, meta=meta, dont_filter=True)

    def _parse_html(self, response):
        """
        解析页面结构 如果页面发生问题则抛出异常，否则返回一个字典
        :param response:
        :return: 返回None表示确实没有数据 否则返回 dict{'total_count': int, 'items': []}
        """
        pager = response.xpath("//div[@class='pagerTitleCell']//text()").extract_first(None)
        # 爬取页面结构失败，则报错
        if pager is None:
            raise IdentifyingCodeError('出现验证码')
        total_count = self._get_total_count(pager)
        item = NumberItem()
        item['name'] = self.request_datum
        item['number'] = total_count
        return item

    def _get_total_count(self, num_str):
        # 正则提取，并转换成整型
        pager = re.search(self.pattern, num_str)
        pager = re.sub(',', '', pager.group(0))
        total_count = int(pager)
        return total_count

    @property
    def cookie_dirty(self):
        return self._cookie_dirty

    @property
    def cookie(self):
        return self._cookie

    @cookie.setter
    def cookie(self, cookie):
        self._cookie = cookie
        self._cookie_dirty = False

    @property
    def request_datum(self):
        """获取队列首部的元素"""
        return self.params.request_queue[0]

    @property
    def request_queue_empty(self):
        """只有请求队列和错误队列中同时为空，才代表空"""
        return len(self.params.request_queue) == 0 and len(self.params.error) == 0

    @property
    def cur_page(self):
        return self.params.cur_page

    def request_error(self):
        return self.params.request_error()
