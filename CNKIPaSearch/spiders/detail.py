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
    # 该配置已经移交到外部
    # custom_settings = {
    #     'DOWNLOADER_MIDDLEWARES': {
    #         'CNKIPaSearch.middlewares.GetFromLocalityMiddleware': 543,
    #         'CNKIPaSearch.middlewares.RetryOrErrorMiddleware': 550,
    #         'CNKIPaSearch.middlewares.ProxyMiddleware': 843,
    #     },
    #     'ITEM_PIPELINES': {
    #         'CNKIPaSearch.pipelines.SaveHtmlPipeline': 300,
    #         'CNKIPaSearch.pipelines.FilterPipeline': 301,
    #         # 'CNKIPaSearch.pipelines.MySQLDetailPipeline': 302,
    #         'CNKIPaSearch.pipelines.SaveJsonPipeline': 303,
    #     }
    # }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        # 使用哪个
        spider = cls(*args, **kwargs)
        spider._set_crawler(crawler)
        return spider

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.pattern = re.compile(r'.*?【(.*?)】.*?')
        # 连续出错计数器
        self.err_count = 0
        # self.base_url = 'http://dbpub.cnki.net/grid2008/dbpub/detail.aspx'
        self.base_url = 'http://nvsm.cnki.net/KCMS/detail/detail.aspx'
        self.basedir = None

    def start_requests(self):
        self.basedir = self.settings.get('DETAIL_DIR')
        for datum in self._get_links():
            yield self._create_request(datum)

    def _get_links(self):
        """
        遍历文件夹，找出还未访问过的页面，之后yield
        :return:
        """
        # 获取链接
        page_dir = os.path.join(self.settings.get('PAGE_DIR'), 'json')
        # 遍历整个文件夹
        for parent, dirnames, filenames in os.walk(page_dir, followlinks=True):
            # 获取前缀路径，和page爬虫保持一致
            common_prefix = os.path.commonprefix([parent, page_dir])
            prefix_path = parent[len(common_prefix)+1:]
            # 遍历所有的文件
            for filename in filenames:
                full_filename = os.path.join(parent, filename)
                # TODO:HTML保存路径和detail保存路径 (路径其他地方不能出现json)
                # 打开该文件
                fp = open(full_filename, 'r', encoding='utf-8')
                json_data = json.load(fp)
                fp.close()
                # 解析并yield
                for datum in json_data:
                    datum['prefix_path'] = prefix_path
                    yield datum
                self.logger.info('File[%s] has loaded' % full_filename)

    def _create_request(self, datum):
        params = {'dbcode': 'scpd', 'dbname': datum['dbname'], 'filename': datum['filename']}
        url = '%s?%s' % (self.base_url, urlencode(params))
        meta = {
            'prefix_path': datum['prefix_path'],
            'title': datum['title'],
            'max_retry_times': self.crawler.settings.get('MAX_RETRY_TIMES'),
            'publication_number': datum['filename'],
        }
        return Request(url=url, callback=self.parse, meta=meta)

    def parse(self, response, **kwargs):
        item = PatentItem()
        item['response'] = response
        item['title'] = response.meta['title']
        item['prefix_path'] = response.meta['prefix_path']
        try:
            # 解析页面结构
            content_div = response.xpath('//div[@class="brief"]')
            # 结构化数据
            row_list = content_div.xpath('./div[@class="row"]')
            # 页面结构出现问题，报错
            if len(row_list) is 0:
                raise ValueError('not found //div[@class="brief"]/div[@class="row"]')
            row_index = 0
            while row_index < len(row_list):
                # 检测是否存在<div class="row-1"> 的节点，是则扩充
                row = row_list[row_index]
                # 解析
                key = row.xpath('./span/text()').re_first(r'\s*(.*?)：.*')
                values = row.xpath('./p[@class="funds"]//text()').extract()
                # 未解析出键值对，必有子节点
                if key is None and len(values) == 0:
                    row_1 = row.xpath('./div[@class="row-1"]')
                    row_2 = row.xpath('./div[@class="row-2"]')
                    if len(row_1) == 1 and len(row_2) == 1:
                        row_list.append(row_1[0])
                        row_list.append(row_2[0])
                    # else:
                    #     self.logger.error('%s页面解析出错:' % (response.meta['title']))
                else:
                    real_key = PatentItem.mapping[key]
                    values = [value.strip() for value in values if value.strip() != 0]
                    item[real_key] = ''.join(values).strip()
                row_index += 1
            # 标题、摘要、主权项
            # title = content_div.xpath('./div[@class="wx-tit"]/h1/text()').extract()
            sovereignty = content_div.css('.claim-text::text').extract()
            summary = content_div.css('.abstract-text::text').extract()
            item['sovereignty'] = ''.join(sovereignty).strip()
            item['summary'] = ''.join(summary).strip()
            yield item
            self.err_count = 0
        # 页面解析错误，重试
        except Exception as e:
            self.logger.error('%s页面解析出错: %s, 重试' % (response.meta['title'], e))
            # TODO:当出错超过5次后，则睡眠一段时间后再请求
            self.err_count += 1
            if self.err_count >= 5:
                self.logger.error('出错次数为%d，睡眠10 s' % self.err_count)
                self.err_count = 0
                time.sleep(10)
