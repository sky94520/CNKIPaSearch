# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import re
import os
import json


def get_path(spider, path_name):
    basedir = spider.settings.get('BASEDIR')
    value = list(spider.request_datum.values())[0]
    variable = re.sub('/', '-', value)
    path = os.path.join(basedir, 'files', path_name, variable)

    return path


class JsonPipeline(object):

    def process_item(self, item, spider):
        path = get_path(spider, 'page_links')
        index = spider.cur_page

        if not os.path.exists(path):
            os.makedirs(path)

        filename = os.path.join(path, '%s.json' % index)
        with open(filename, "w", encoding='utf-8') as fp:
            fp.write(json.dumps(item['array'], ensure_ascii=False, indent=2))
        return item


class SavePagePipeline(object):

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
        return
