# -*- coding: utf-8 -*-
import re
import math
import scrapy
from urllib.parse import urlencode, urlparse, parse_qsl
from . import IdentifyingCodeError
from ..items import SearchItem
from ..params.PagePersistParam import PagePersistParam
from ..hownet_config import BaseConfig


class PageSpider(scrapy.Spider):
    name = 'page'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'CNKIPaSearch.middlewares.GetFromLocalityMiddleware': 543,
            'CNKIPaSearch.middlewares.RetryOrErrorMiddleware': 550,
            'CNKIPaSearch.middlewares.ProxyMiddleware': 843,
            'CNKIPaSearch.middlewares.CookieMiddleware': 844,
        },
        'ITEM_PIPELINES': {
            'CNKIPaSearch.pipelines.SaveSearchJsonPipeline': 300,
            'CNKIPaSearch.pipelines.SaveSearchHtmlPipeline': 301,
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pattern = r'\d+(\,\d+)*'
        # 是否请求新的cookie
        self._cookie_dirty, self._cookie = True, None
        self.params = None
        self.basedir = None

    def start_requests(self):
        """
        scrapy会调用该函数获取Request
        :return: yield request or return None
        """
        self.basedir = self.settings.get('PAGE_DIR')
        self.logger.info('the file path is %s', self.basedir)
        self.params = PagePersistParam(self.basedir)
        if self.request_queue_empty:
            return None
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
            item, total_count = self._parse_html(response)
        except IdentifyingCodeError as e:
            self.logger.error(e)
            self._cookie_dirty = True
            yield self._create_request(self.params.cur_page)
            return
        # 发出请求，获取年份 专利数量
        if total_count > self.settings.get('MAX_PATENT_NUM'):
            yield self._create_group_request()
            return
        max_page = min(120,
                       math.ceil(total_count / self.settings.get('PATENT_NUMBER_PER_PAGE', 50)))
        # 返回items
        yield item
        # 开启新的请求
        self.params.cur_page += 1
        # 该任务爬取完成，重新请求cookie
        if self.params.cur_page > max_page:
            self._cookie_dirty = True
            self.params.request_success()
        # 回写checkpoint
        self.params.save()
        if self.request_queue_empty:
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
            'max_retry_times': self.crawler.settings.get('MAX_RETRY_TIMES'),
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
        self.logger.info('the total count is %d' % total_count)
        # 专利条目数组
        tr_list = response.xpath("//table[@class='GridTableContent']//tr")
        length = len(tr_list)
        # 这个分类的当前页面条目个数确实为0 爬取完成
        if length == 0:
            return None
        item = SearchItem()
        item['response'] = response
        item['array'] = []
        # 解析条目 去掉头
        for index in range(1, length):
            tr = tr_list[index]
            # 链接
            link = tr.xpath('./td[2]/a/@href').extract_first()
            parse_result = urlparse(link)
            query_tuple = parse_qsl(parse_result[4])
            datum = {}
            # 键值对 映射
            for t in query_tuple:
                if t[0] in SearchItem.KEYS:
                    datum[t[0]] = t[1]
            # TODO: 外部扩展
            titles = tr.xpath('./td[2]/a//text()').extract()
            datum['title'] = ''.join(titles)
            datum['inventor'] = tr.xpath('./td[3]/text()').extract_first()
            applicants = tr.xpath('./td[4]//text()').extract()
            datum['applicants'] = ''.join(applicants)
            datum['application_date'] = tr.xpath('./td[5]/text()').extract_first()
            datum['publication_date'] = tr.xpath('./td[6]/text()').extract_first()

            item['array'].append(datum)

        return item, total_count

    def _get_total_count(self, num_str):
        # 正则提取，并转换成整型
        pager = re.search(self.pattern, num_str)
        pager = re.sub(',', '', pager.group(0))
        total_count = int(pager)
        return total_count

    def _create_group_request(self):
        """
        创建一个请求 用于获取年份 专利数据 年份对应的专利数据 按公开日统计得到
        :return: request 返回请求
        """
        # TODO: 暂时不知道Param代表的意思
        params = {
            'action': 1,
            'Param': "ASP.brief_result_aspx#SCPD/%u5E74/%u5E74,count(*)/%u5E74/(%u5E74,'date')#%u5E74$desc/1000000$/-/40/40000/ButtonView",
            'cid': 1,
            'clayer': 0,
            '__': BaseConfig._get_now_gmt_time()
        }
        base_url = 'http://kns.cnki.net/kns/group/doGroupLeft.aspx'
        url = '%s?%s' % (base_url, urlencode(params))
        meta = {
            'max_retry_times': self.crawler.settings.get('MAX_RETRY_TIMES')
        }
        return scrapy.Request(url=url, callback=self._parse_group, meta=meta, dont_filter=True)

    def _parse_group(self, response):
        span_list = response.xpath('.//span')
        years, numbers = [], []
        for idx, span in enumerate(span_list):
            # 奇数为年份，偶数为数字
            if idx % 2 == 0:
                year = int(span.xpath('./a/text()').extract_first(0))
                years.append(year)
            else:
                number_str = span.xpath('./text()').extract_first("(0)")
                number = int(number_str[1:-1])
                numbers.append(number)
        # 交给PersistParam
        print(years, numbers)
        self.params.set_groups(years, numbers, self.settings.get('MAX_PATENT_NUM'))
        # 写入，并重新发起请求
        self.params.save()
        self._cookie_dirty = True
        yield self._create_request(self.params.cur_page)

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
        if len(self.params.request_queue) == 0:
            self.params.pop_from_error_queue()
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
