# -*- coding: utf-8 -*-
import scrapy
import os
import re
import json
import time
from urllib.parse import urlencode

from scrapy import Request
from ..items import PatentItem


class DetailSpider(scrapy.Spider):
    name = 'detail'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'CNKIPaSearch.middlewares.GetFromLocalityMiddleware': 543,
            'CNKIPaSearch.middlewares.RetryOrErrorMiddleware': 550,
            'CNKIPaSearch.middlewares.ProxyMiddleware': 843,
        },
        'ITEM_PIPELINES': {
            'CNKIPaSearch.pipelines.SaveDetailHtmlPipeline': 300,
            'CNKIPaSearch.pipelines.FilterPipeline': 301,
            'CNKIPaSearch.pipelines.MySQLDetailPipeline': 302,
            # 'CNKIPaSearch.pipelines.SaveDetailJsonPipeline': 303,
        }
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        # 使用哪个
        spider = cls(*args, **kwargs)
        spider._set_crawler(crawler)
        return spider

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pattern = re.compile(r'.*?【(.*?)】.*?')
        # 连续出错计数器
        self.err_count = 0
        self.base_url = 'http://dbpub.cnki.net/grid2008/dbpub/detail.aspx'

    def start_requests(self):
        for datum in self._get_links():
            yield self._create_request(datum)

    def _get_links(self):
        """
        遍历文件夹，找出还未访问过的页面，之后yield
        :return:
        """
        # 获取链接
        basedir = self.settings.get('BASEDIR')
        pending_path = os.path.join(basedir, 'files', 'page_links')
        # 遍历整个文件夹
        for parent, dirnames, filenames in os.walk(pending_path, followlinks=True):
            # 遍历所有的文件
            for filename in filenames:
                full_filename = os.path.join(parent, filename)
                # HTML保存路径和detail保存路径
                html_path = re.sub('page_links', 'html', parent)
                detail_path = re.sub('page_links', 'detail', parent)
                # 打开该文件
                fp = open(full_filename, 'r', encoding='utf-8')
                json_data = json.load(fp)
                fp.close()
                # 解析并yield
                for datum in json_data:
                    datum['html_path'] = html_path
                    datum['detail_path'] = detail_path
                    yield datum
                self.logger.info('File[%s] has loaded' % filename)

    def _create_request(self, datum):
        params = {'dbcode': 'scpd', 'dbname': datum['dbname'], 'filename': datum['filename']}
        url = '%s?%s' % (self.base_url, urlencode(params))
        meta = {
            'html_path': datum['html_path'],
            'detail_path': datum['detail_path'],
            'title': datum['title'],
            'max_retry_times': self.crawler.settings.get('MAX_RETRY_TIMES'),
            'publication_number': datum['filename'],
        }
        return Request(url=url, callback=self.parse, meta=meta)

    def parse(self, response):
        item = PatentItem()
        item['response'] = response
        item['title'] = response.meta['title']
        try:
            # 解析页面结构
            tr_list = response.xpath('//table[@id="box"]/tr')
            tr_index, tr_length = 0, len(tr_list)
            # 页面结构出现问题，报错
            if tr_length is 0:
                raise ValueError('not found table[@id="box"]')
            # 去掉最后一个tr 最后一个tr
            while tr_index < tr_length:
                td_list = tr_list[tr_index].xpath('./td')
                index, length, real_key = 0, len(td_list), None

                while index < length:
                    # 提取出文本
                    text_list = td_list[index].xpath('.//text()').extract()
                    text = ''.join(text_list).strip()
                    # 已经有key，则text为对应的value
                    if real_key:
                        item[real_key], real_key = text, None
                    # 过滤掉长度为0的键
                    elif len(text) > 0:
                        # 正则未提取到任何值 则键发生问题
                        result = re.search(self.pattern, text)
                        if result is None:
                            if real_key is not None:
                                raise
                        else:
                            key = result.group(1)
                            # 对应的键 没有则跳过下一个
                            if key in PatentItem.mapping:
                                real_key = PatentItem.mapping[key]
                            else:
                                index += 1
                    index += 1
                tr_index += 1
            yield item
            self.err_count = 0
        # 页面解析错误，重试
        except Exception as e:
            self.logger.error('%s页面解析出错: %s, 重试' % (response.meta['title'], e))
            # TODO:当出错超过5次后，则睡眠5min后再请求
            self.err_count += 1
            if self.err_count >= 5:
                self.err_count = 0
                self.logger.error('出错次数为%d，睡眠10 s' % self.err_count)
                time.sleep(10)

