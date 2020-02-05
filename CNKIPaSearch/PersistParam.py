"""
author: xiaoniu
date: 2020-02-04
desc: 持久化变量，主要用在Page参数内的一些持久化变量
比如当前的待请求队列，当前页面
"""
import os
import json


class PersistParam(object):

    def __init__(self, basedir):
        self.basedir = basedir
        self.filename = os.path.join(self.basedir, 'files', 'checkpoint')
        self.cur_page = 1
        self.request_queue = None  # 队首元素作为当前进行元素
        self.done = []
        self.error = []  # 错误的数据
        # 进行加载数据
        self.load()

    def load(self):
        # 文件不存在，则尝试从文件夹中读取
        if not os.path.isfile(self.filename):
            self.request_queue = self._load_from_dir()
            return
        fp = open(self.filename, 'r', encoding='utf-8')
        json_data = json.load(fp)
        fp.close()
        self.cur_page = json_data.get('cur_page', 1)
        self.request_queue = json_data.get('request_queue', [])
        self.done = json_data.get('done', [])
        self.error = json_data.get('error', [])

    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as fp:
            json.dump({
                'cur_page': self.cur_page,
                'request_queue': self.request_queue,
                'done': self.done,
                'error': self.error,
            }, fp, ensure_ascii=False, indent=1)

    def request_success(self):
        """
        从请求队列中删除队首的元素，并存放在self.done数组中
        """
        top = self.request_queue.pop(0)
        self.done.append(top)
        self.cur_page = 1
        return top

    def request_error(self):
        """
        保存当前的现场，待以后处理
        :return: 返回爬取失败的数据
        """
        top = self.request_queue.pop(0)
        self.error.append({'values': top, 'cur_page': self.cur_page})
        self.cur_page = 1
        return top

    def _load_from_dir(self):
        queue = []

        path = os.path.join(self.basedir, 'files', 'pending')
        # 遍历整个page_links文件夹
        for parent, dirnames, filenames in os.walk(path, followlinks=True):
            # 遍历所有的文件
            for filename in filenames:
                full_filename = os.path.join(parent, filename)
                with open(full_filename, 'r', encoding='utf-8') as fp:
                    queue.extend(json.load(fp))
        return queue
