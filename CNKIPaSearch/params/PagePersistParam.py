"""
author: xiaoniu
date: 2020-02-04
desc: 持久化变量，主要用在Page参数内的一些持久化变量
比如当前的待请求队列，当前页面
"""
import os
import json
import logging
import shutil
from datetime import datetime, timedelta
from CNKIPaSearch.utils import date2str, str2date
from CNKIPaSearch.hownet_config import FROM_DATE_KEY, TO_DATE_KEY


class PagePersistParam(object):
    """用于page.py的持久化"""
    def __init__(self, basedir):
        self.basedir = basedir
        # 保存中断
        self.filename = os.path.join(self.basedir, 'files', 'page_checkpoint.json')
        self.cur_page = 1
        self.request_queue = None  # 队首元素作为当前进行元素
        self.error = []  # 错误的数据
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
        self.cur_page = json_data.get('cur_page', 1)
        self.request_queue = json_data.get('request_queue', [])
        self.error = json_data.get('error', [])
        # 存在checkpoint，但是已经全部读取完成，则重新遍历文件夹
        if len(self.request_queue) == 0 and len(self.error) == 0:
            self.request_queue = self._load_from_dir()

    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as fp:
            json.dump({
                'cur_page': self.cur_page,
                'request_queue': self.request_queue,
                'error': self.error,
            }, fp, ensure_ascii=False, indent=1)

    def request_success(self):
        """
        从请求队列中删除队首的元素
        """
        top = self.request_queue.pop(0)
        self.cur_page = 1
        return top

    def set_groups(self, years, numbers, maximum):
        """
        根据年份和专利数量，把队首元素进行拆分，以使得能完全爬取
        :param years: 年份
        :param numbers: 随年份变化的数量
        :param maximum: 最大值
        :return:
        """
        top = self.request_queue.pop(0)
        count, from_year = 0, None
        now = datetime.now()
        idx = 0
        while idx < len(years) and idx < len(numbers):
            year = years[idx]
            count += numbers[idx]
            if idx + 1 < len(years) and idx + 1 < len(numbers):
                number = numbers[idx+1]
            else:
                number = maximum
            if from_year is None:
                from_year = year

            if count > maximum:
                if FROM_DATE_KEY in top and TO_DATE_KEY in top:
                    from_date, to_date = str2date(top[FROM_DATE_KEY]), str2date(top[TO_DATE_KEY])
                else:
                    from_date, to_date = datetime(year, 1, 1), (now if year == now.year else datetime(year, 12, 31))
                delta = (to_date - from_date) / 2
                j, dates = 0, [from_date, from_date + delta, from_date + delta + timedelta(1), to_date]
                while j < len(dates):
                    datum = top.copy()
                    datum[FROM_DATE_KEY] = date2str(date=dates[j])
                    datum[TO_DATE_KEY] = date2str(date=dates[j+1])
                    j += 2
                    self.request_queue.insert(0, datum)
                count, from_year = 0, None
            elif count + number > maximum:
                datum = top.copy()
                datum[FROM_DATE_KEY] = date2str(year=from_year)
                if year == now.year:
                    datum[TO_DATE_KEY] = date2str(date=now)
                else:
                    datum[TO_DATE_KEY] = date2str(date=datetime(year, 12, 31))
                self.request_queue.insert(0, datum)
                count, from_year = 0, None
            idx += 1

    def request_error(self):
        """
        保存当前的现场，待以后处理
        :return: 返回爬取失败的数据
        """
        top = self.request_queue.pop(0)
        self.error.append({'values': top, 'cur_page': self.cur_page})
        self.cur_page = 1
        return top

    def pop_from_error_queue(self):
        top = self.error.pop(0)
        self.cur_page = top['cur_page']
        self.request_queue.append(top['values'])

    def _load_from_dir(self):
        queue = []
        path = os.path.join(self.basedir, 'files', 'page_pending')
        if not os.path.exists(path):
            logging.warning('%s not exists' % path)
            return []

        another_path = os.path.join(self.basedir, 'files', 'page_read')
        # 遍历整个page_links文件夹 得到待移动的文件
        moving_files = []
        for parent, dirnames, filenames in os.walk(path, followlinks=True):
            # 遍历所有的文件
            for filename in filenames:
                full_filename = os.path.join(parent, filename)
                with open(full_filename, 'r', encoding='utf-8') as fp:
                    queue.extend(json.load(fp))
                moving_files.append(full_filename)
        self.save()
        # 移动文件
        if not os.path.exists(another_path):
            os.makedirs(another_path)
        for moving_file in moving_files:
            # 存在文件
            try:
                shutil.move(moving_file, another_path)
            except Exception as e:
                logging.warning(e)
            if os.path.exists(moving_file):
                os.remove(moving_file)
        return queue
