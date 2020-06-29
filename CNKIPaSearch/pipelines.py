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
from CNKIPaSearch.config import MYSQL_CONFIG
from CNKIPaSearch.utils.batch import import_patent


logger = logging.getLogger(__name__)


def get_path(spider, path_name):
    # basedir = spider.settings.get('BASEDIR')
    basedir = spider.basedir
    # 数据中含有存在键dirname，那么就以对应的值作为文件名
    if 'dirname' in spider.request_datum:
        dirname = spider.request_datum['dirname']
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
        self.array_keys = ['inventor', 'patent_cls_number', 'agent', 'applicant', 'joint_applicant']
        # TODO:字符串转为datetime
        # self.date_keys = ['application_date', 'publication_date']
        self.date_keys = []
        # 去多个换行
        self.text_keys = ['sovereignty', 'summary']
        self.pattern = re.compile(r'[\n|\r]+')
        # 转成int
        self.int_keys = ['page_number']

    def process_item(self, item, spider):
        try:
            for key, value in item.items():
                if key in self.array_keys:
                    item[key] = []
                    for v in value.split(';'):
                        if len(v) > 0:
                            item[key].append(v)
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
        self.pattern = re.compile(r'[\n|\r]+')

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
        if not os.path.exists(path):
            os.makedirs(path)

        filename = os.path.join(path, '%s.json' % item['publication_number'])
        with open(filename, "w", encoding='utf-8') as fp:
            fp.write(json.dumps(dict(item), ensure_ascii=False, indent=2))
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

    def process_item(self, item, spdier):
        copy = dict(item)
        query = self.db_pool.runInteraction(import_patent, copy, self.handle_success)
        query.addErrback(self.handle_error)
        return DropItem()

    def handle_success(self, item):
        """插入数据库成功，才创建文件"""
        path = self.save_path
        if not os.path.exists(path):
            os.makedirs(path)

        filename = os.path.join(path, '%s.json' % item['publication_number'])
        with open(filename, "w", encoding='utf-8') as fp:
            fp.write(json.dumps(dict(item), ensure_ascii=False, indent=2))
        return item

    def handle_error(self, failure):
        name = threading.current_thread().name
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
        # 读取断点数据
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        elif os.path.exists(self.filename):
            fp = open(self.filename, 'r')
            reader = csv.DictReader(fp, fieldnames=self.fieldnames)
            for idx, datum in enumerate(reader):
                if idx == 0:
                    continue
                datum['number'] = int(datum['number'])
                self.json_data.append(datum)
            fp.close()

    def process_item(self, item, spider):
        self.json_data.append({
            'name': item['name']['applicant'],
            'number': item['number'],
        })
        # TODO: 每次都写入
        sorted(self.json_data, key=lambda x: x['number'], reverse=True)
        fp = open(self.filename, 'w', encoding='gb2312', newline='')
        writer = csv.DictWriter(fp, fieldnames=self.fieldnames)
        writer.writeheader()
        writer.writerows(self.json_data)
        fp.close()
        return item

    def close_spider(self, spider):
        pass
