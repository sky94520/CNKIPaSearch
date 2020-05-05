# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import re
import os
import csv
import json
import pymongo
import logging
import operator
import datetime
from scrapy.exceptions import DropItem
from .items import PatentItem


logger = logging.getLogger(__name__)


def get_path(spider, path_name):
    basedir = spider.settings.get('BASEDIR')
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
    path = os.path.join(basedir, 'files', path_name, dirname)

    return path


class SaveSearchJsonPipeline(object):

    def process_item(self, item, spider):
        # 不存在专利，则直接退出
        if len(item['array']) == 0:
            response = item['response']
            raise DropItem('%s has not any patent' % response.url)
        path = get_path(spider, 'page_links')
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
        path = get_path(spider, 'page')
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
        except Exception as e:
            # 在解析时出现错误，则报错后移除该item
            logger.error('process [%s] error: %s' % (item['publication_number'], e))
            raise DropItem()

        return item


class SaveDetailHtmlPipeline(object):
    def process_item(self, item, spider):
        response = item['response']
        # 该文件从本地获取，不再重新保存
        if 'load_from_local' in response.meta and response.meta['load_from_local']:
            return item

        path = response.meta['html_path']
        publication_number = response.meta['publication_number']

        if not os.path.exists(path):
            os.makedirs(path)

        filename = os.path.join(path, '%s.html' % publication_number)
        with open(filename, "wb") as fp:
            fp.write(response.body)
        return item


class SaveDetailJsonPipeline(object):
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            basedir=crawler.settings.get('BASEDIR'),
        )

    def __init__(self, basedir):
        self.save_path = os.path.join(basedir, 'files', 'detail')
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

    def process_item(self, item, spider):
        path = self.save_path
        if 'response' in item:
            path = item['response'].meta['detail_path']
            del item['response']

        if not os.path.exists(path):
            os.makedirs(path)

        filename = os.path.join(path, '%s.json' % item['publication_number'])
        with open(filename, "w", encoding='utf-8') as fp:
            fp.write(json.dumps(dict(item), ensure_ascii=False, indent=2))
        return item


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


class MongoPipeline(object):
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.client = None
        self.db = None
        # 缓冲区 一定数量则填充一次
        self.buffer = []

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DB')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def process_item(self, item, spdier):
        # 通过application_number保证唯一
        collection = self.db[item.collection]
        result = collection.find_one({'publication_number': item['publication_number']}, {'_id': 1})
        if result is not None:
            raise DropItem('the %s has already saved in database' % item['publication_number'])
        cur_count, max_count = spdier.counter[item['source']]
        # 只有在该json文件全部链接都爬取完成的时候，才会写入到redis中
        if cur_count + 1 >= max_count:
            spdier.db.sadd('page_links', item['source'])
            spdier.counter.pop(item['source'])
        else:
            spdier.counter[item['source']] = (cur_count + 1, max_count)

        del item['source']
        self.buffer.append(dict(item))
        # 每1000个数据写入到数据库中
        if len(self.buffer) >= 100:
            self.db[PatentItem.collection].insert_many(self.buffer)
            self.buffer.clear()
        # 不返回item，则不再输出到控制台
        # return item

    def close_spider(self, spider):
        if len(self.buffer) > 0:
            self.db[PatentItem.collection].insert_many(self.buffer)
            self.buffer.clear()
        self.client.close()

