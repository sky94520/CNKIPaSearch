"""
该爬虫仅仅从本地获取detail文件，
并保存到数据库
"""
import os
import json
import scrapy
from scrapy import Request

from ..utils import read_files_from_path
from ..items import PatentItem


class PatentSpider(scrapy.Spider):
    name = 'patent'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'CNKIPaSearch.middlewares.LoadJsonFromLocalityMiddleware': 543,
        },
        'ITEM_PIPELINES': {
            'CNKIPaSearch.pipelines.MySQLDetailPipeline': 302,
        }
    }

    def start_requests(self):
        self.basedir = self.settings.get('DETAIL_DIR')
        generator = read_files_from_path(self.basedir, suffix='json')
        for path, filename in generator:
            yield self._create_request(path, filename)

    def parse(self, response, **kwargs):
        # 提取json
        json_data = json.loads(response.text)
        item = PatentItem()
        for key, value in json_data.items():
            item[key] = value
        yield item

    def _create_request(self, path, filename):
        """创建虚拟请求"""
        publication_number = os.path.splitext(filename)[0]
        url = '%s?%s' % ('http://127.0.0.1:5050', publication_number)
        meta = {
            'max_retry_times': self.crawler.settings.get('MAX_RETRY_TIMES'),
            'publication_number': publication_number,
            'path': path
        }
        return Request(url=url, callback=self.parse, meta=meta)
