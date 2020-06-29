# -*- coding: utf-8 -*-
import os
import re
import time
import json
import scrapy
from scrapy import Request
from urllib.parse import urljoin
from ..items import StatusItem


class StatusSpider(scrapy.Spider):
    name = 'status'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'CNKIPaSearch.middlewares.GetFromLocalityMiddleware': 543,
            'CNKIPaSearch.middlewares.UserAgentMiddleware': 544,
            'CNKIPaSearch.middlewares.RetryOrErrorMiddleware': 550,
            'CNKIPaSearch.middlewares.ProxyMiddleware': 843,
        },
        'ITEM_PIPELINES': {
            'CNKIPaSearch.pipelines.SaveHtmlPipeline': 300,
            'CNKIPaSearch.pipelines.FilterArrayPipeline': 301,
            'CNKIPaSearch.pipelines.SaveJsonPipeline': 303,
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.err_count = 0
        self.base_url = 'https://dbpub.cnki.net/GBSearch/SCPDGBSearch.aspx'
        self.basedir = None

    def start_requests(self):
        self.basedir = self.settings.get('STATUS_DIR')
        for datum in self._get_links():
            yield self._create_request(datum)

    def parse(self, response):
        item = StatusItem()
        item['response'] = response
        item['publication_number'] = response.meta['publication_number']
        item['prefix_path'] = response.meta['prefix_path']
        try:
            tr_list = response.css('table.state tr')
            # 页面结构出现问题，报错
            if len(tr_list) is 0:
                raise ValueError('not found table[@class="state"]')
            array = []
            # 去掉最后一个tr 最后一个tr
            for tr_index, tr in enumerate(tr_list):
                if tr_index == len(tr_list)-1:
                    continue
                td_list = tr_list[tr_index].xpath('./td')
                datum = {}
                if len(td_list) == 0:
                    continue
                for index, td in enumerate(td_list):
                    text_list = td_list[index].xpath('.//text()').extract()
                    text = ''.join(text_list).strip()
                    datum[item.KEYS[index]] = text
                array.append(datum)
            item['array'] = array
            yield item
        # 页面解析错误，重试
        except Exception as e:
            self.logger.error('%s页面解析出错: %s, 重试' % (response.meta['publication_number'], e))
            # TODO:当出错超过5次后，则睡眠后再请求
            self.err_count += 1
            if self.err_count >= 5:
                self.err_count = 0
                self.logger.error('出错次数为%d，睡眠10 s' % self.err_count)
                time.sleep(10)

    def _create_request(self, datum):
        url = urljoin(self.base_url, '?ID=%s' % datum['application_number'])
        meta = {
            'prefix_path': datum['prefix_path'],
            'max_retry_times': self.crawler.settings.get('MAX_RETRY_TIMES'),
            'publication_number': datum['publication_number'],
        }
        return Request(url=url, callback=self.parse, meta=meta)

    def _get_links(self):
        """
        遍历文件夹，找出还未访问过的页面，之后yield
        :return:
        """
        # 获取链接
        detail_dir = os.path.join(self.settings.get('DETAIL_DIR'), 'json')
        # 遍历整个文件夹
        for parent, dirnames, filenames in os.walk(detail_dir, followlinks=True):
            # 获取前缀路径，和page爬虫保持一致
            common_prefix = os.path.commonprefix([parent, detail_dir])
            prefix_path = parent[len(common_prefix)+1:]
            # 遍历所有的文件
            for filename in filenames:
                full_filename = os.path.join(parent, filename)
                # 打开该文件
                fp = open(full_filename, 'r', encoding='utf-8')
                json_data = json.load(fp)
                fp.close()
                # 解析并yield
                datum = {
                    'prefix_path': prefix_path,
                    'application_number': json_data['application_number'],
                    'publication_number': json_data['publication_number']
                }
                yield datum
                self.logger.info('File[%s] has loaded' % full_filename)
