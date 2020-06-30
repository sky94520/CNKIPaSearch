import os
import json
import logging


class TurnPersistParam(object):
    """用于run_page_and_detail.py的持久化"""
    def __init__(self, basedir):
        self.basedir = basedir
        # 保存中断
        self.filename = os.path.join(self.basedir, 'files', 'checkpoint.json')
        self.request_queue = []  # 队首元素作为当前进行元素
        # 进行加载数据
        self.load()

    def load(self):
        # 文件不存在，则尝试从文件夹中读取
        if not os.path.exists(self.filename):
            self.request_queue = self._load_from_dir()
            return
        fp = open(self.filename, 'r', encoding='utf-8')
        json_data = json.load(fp)
        fp.close()
        self.request_queue = json_data.get('request_queue', [])
        # 存在checkpoint，但是已经全部读取完成，则重新遍历文件夹
        if len(self.request_queue) == 0:
            self.request_queue = self._load_from_dir()
        self._save()

    def pop(self):
        """
        从请求队列中删除队首的元素，并回写到文件
        """
        top = self.request_queue.pop(0)
        self._save()
        return top

    def _save(self):
        with open(self.filename, 'w', encoding='utf-8') as fp:
            json.dump({
                'request_queue': self.request_queue},
                fp, ensure_ascii=False, indent=1)

    def _load_from_dir(self):
        queue = []
        path = os.path.join(self.basedir, 'files', 'pending')
        if not os.path.exists(path):
            logging.warning('%s:%s not exists' % (__file__, path))
            return []
        # 遍历整个page_links文件夹 得到待移动的文件
        for parent, dirnames, filenames in os.walk(path, followlinks=True):
            # 遍历所有的文件
            for filename in filenames:
                full_filename = os.path.join(parent, filename)
                with open(full_filename, 'r', encoding='utf-8') as fp:
                    queue.extend(json.load(fp))
        return queue
