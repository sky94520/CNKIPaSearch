# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import re
import os
import csv
import json
import logging
import datetime
import threading
from pymysql import cursors
from twisted.enterprise import adbapi
from scrapy.exceptions import DropItem

from config import MYSQL_CONFIG
from .spiders.patent import PatentSpider
from .utils import write_json
from CNKIPaSearch.utils.patent import import_patent


logger = logging.getLogger(__name__)


def get_path(spider, path_name):
    """只有page使用的过滤器才会调用该函数"""
    basedir = spider.basedir
    # 数据中含有存在键dirname，那么就以对应的值作为文件名
    if 'dirname' in spider.request_datum:
        dirname = spider.request_datum['dirname']
        # 加上date-gkr-from date-gkr-to
        name = ''
        if 'date_gkr_from' in spider.request_datum:
            name = spider.request_datum['date_gkr_from']
        if 'date_gkr_to' in spider.request_datum:
            name = '%s %s' % (name, spider.request_datum['date_gkr_to'])
        if len(name) != 0:
            dirname = os.path.join(dirname, name)
    else:
        # 以第一个作为文件名， 其他作为另外的文件名
        values = list(spider.request_datum.values())
        # 必定存在一个键值对
        dirname = re.sub('/', '-', values[0])
        if len(values) > 1:
            dirname = os.path.join(dirname, ','.join(values[1:]))
    path = os.path.join(basedir, path_name, dirname)
    return path


class SaveSearchJsonPipeline(object):

    def process_item(self, item, spider):
        # 不存在专利，则直接退出
        if len(item['array']) == 0:
            response = item['response']
            raise DropItem('%s has not any patent' % response.url)
        path = get_path(spider, 'json')
        index = spider.cur_page

        if not os.path.exists(path):
            os.makedirs(path)

        filename = os.path.join(path, '%s.json' % index)
        with open(filename, "w", encoding='utf-8') as fp:
            fp.write(json.dumps(item['array'], ensure_ascii=False, indent=2))
        return item


class SaveSearchHtmlPipeline(object):
    def process_item(self, item, spider):
        # 文件存储路径
        path = get_path(spider, 'html')
        response = item['response']
        index = spider.cur_page

        if not os.path.exists(path):
            os.makedirs(path)
        filename = os.path.join(path, '%s.html' % index)
        with open(filename, "wb") as fp:
            fp.write(response.body)
        return item


class FilterPipeline(object):
    """清除特殊字符"""
    def __init__(self):
        # 字符串转为数组
        self.array_keys = ['inventor', 'agent', 'applicant', 'joint_applicant']
        # TODO:字符串转为datetime
        # self.date_keys = ['application_date', 'publication_date']
        self.date_keys = []
        # 去多个换行
        self.text_keys = ['sovereignty', 'summary']
        self.pattern = re.compile(r'\s+')
        # 转成int
        self.int_keys = ['page_number']
        # 部 大类 小类 组，比如H01R107/00 或 01-01
        self.cls_pattern = re.compile(r'[A-Z]\d+[A-Z]\d+/\d+|\d+-\d+')

    def process_item(self, item, spider):
        try:
            for key, value in item.items():
                # 数据转化数组
                if key in self.array_keys:
                    item[key] = []
                    for v in value.split(';'):
                        if len(v) > 0:
                            item[key].append(v)
                elif key == 'patent_cls_number':
                    item[key] = re.findall(self.cls_pattern, value)
                elif key in self.date_keys:
                    item[key] = datetime.datetime.strptime(value, '%Y-%m-%d')
                elif key in self.text_keys:
                    item[key] = re.sub(self.pattern, '', value)
                elif key in self.int_keys:
                    item[key] = int(value)
            if 'response' in item:
                del item['response']
        except Exception as e:
            # 在解析时出现错误，则报错后移除该item
            logger.error('process [%s] error: %s' % (item['publication_number'], e))
            raise DropItem()
        return item


class FilterArrayPipeline(object):
    """清除特殊字符"""
    def __init__(self):
        # 去除换行
        self.text_keys = ['information']
        self.pattern = re.compile(r'\s+')

    def process_item(self, item, spider):
        try:
            for idx, datum in enumerate(item['array']):
                for key, value in datum.items():
                    if key in self.text_keys:
                        item['array'][idx][key] = re.sub(self.pattern, ' ', value)
            if 'response' in item:
                del item['response']
        except Exception as e:
            # 在解析时出现错误，则报错后移除该item
            logger.error('process [%s] error: %s' % (item['publication_number'], e))
            raise DropItem()
        return item


class SaveHtmlPipeline(object):
    """detail status 爬虫用"""
    def process_item(self, item, spider):
        response = item['response']
        # 该文件从本地获取，不再重新保存
        if 'load_from_local' in response.meta and response.meta['load_from_local']:
            return item
        # 获取完整路径
        prefix_path = response.meta['prefix_path']
        path = os.path.join(spider.basedir, 'html', prefix_path)
        publication_number = response.meta['publication_number']

        if not os.path.exists(path):
            os.makedirs(path)

        filename = os.path.join(path, '%s.html' % publication_number)
        with open(filename, "wb") as fp:
            fp.write(response.body)
        return item


class SaveJsonPipeline(object):
    """detail status 爬虫使用该过滤器"""
    def process_item(self, item, spider):
        prefix_path = item['prefix_path']
        del item['prefix_path']
        path = os.path.join(spider.basedir, 'json', prefix_path)
        filename = os.path.join(path, '%s.json' % item['application_number'])
        write_json(path, filename, dict(item))
        return item


class MySQLDetailPipeline(object):
    @classmethod
    def from_settings(cls, settings):
        db_pool = adbapi.ConnectionPool('pymysql', cursorclass=cursors.DictCursor, **MYSQL_CONFIG)
        basedir = settings.get('BASEDIR')
        return cls(basedir, db_pool)

    def __init__(self, basedir, pool):
        self.db_pool = pool
        self.save_path = os.path.join(basedir, 'files', 'detail')
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

    def process_item(self, item, spider):
        copy = dict(item)
        # TODO 函数待修改（数据库发生变化）
        query = self.db_pool.runInteraction(import_patent, copy, self.handle_success, spider)
        query.addErrback(self.handle_error)
        return DropItem()

    def handle_success(self, item, spider):
        """在插入数据库成功后，会写入到文件"""
        if isinstance(spider, PatentSpider):
            return
        path = self.save_path
        # 写入文件
        filename = os.path.join(path, '%s.json' % item['application_number'])
        write_json(path, filename, dict(item))
        return item

    def handle_error(self, failure):
        name = threading.current_thread().name
        logger.error(failure)

    def close_spider(self, spider):
        self.db_pool.close()


class MySQLPatentStatusPipeline(object):

    def __init__(self):
        self.db_pool = adbapi.ConnectionPool('pymysql', cursorclass=cursors.DictCursor, **MYSQL_CONFIG)

    def process_item(self, item, spdier):
        copy = dict(item)
        query = self.db_pool.runInteraction(import_patent, copy)
        query.addErrback(self.handle_error)
        return DropItem()

    def handle_error(self, failure):
        """插入数据库失败回调函数"""
        logger.error(failure)

    def close_spider(self, spider):
        self.db_pool.close()


class SaveNumberCsvPipeline(object):
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            basedir=crawler.settings.get('BASEDIR'),
        )

    def __init__(self, basedir):
        # 保存所有名单
        self.fieldnames = ['name', 'number']
        self.json_data = []
        save_path = os.path.join(basedir, 'files')
        self.filename = os.path.join(save_path, 'list_quantity.csv')
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        # 读取，添加，重写(断点保存)
        elif os.path.exists(self.filename):
            fp = open(self.filename, 'r')
            reader = csv.DictReader(fp)
            for idx, datum in enumerate(reader):
                datum['number'] = int(datum['number'])
                self.json_data.append(datum)
            fp.close()

    def process_item(self, item, spider):
        self.json_data.append({
            'name': item['name'],
            'number': item['number'],
        })
        # TODO: 每次都写入
        self.json_data = sorted(self.json_data, key=lambda x: x['number'], reverse=True)
        fp = open(self.filename, 'w', encoding='gb2312', newline='')
        writer = csv.DictWriter(fp, fieldnames=self.fieldnames)
        writer.writeheader()
        writer.writerows(self.json_data)
        fp.close()
        return item

    def close_spider(self, spider):
        pass
