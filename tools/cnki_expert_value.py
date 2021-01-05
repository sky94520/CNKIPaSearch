"""
知网专业搜索表达式构造
输入：行业代码
输出：知网专业搜索表达式
"""
import os
import json
import pymysql

from config import MYSQL_CONFIG
from CNKIPaSearch.settings import PAGE_DIR
from CNKIPaSearch.utils import select, select_one


class CNKIExpertSearch(object):
    """CNKI 专家搜索"""
    def __init__(self):
        self.connection = pymysql.connect(**MYSQL_CONFIG)

    def __del__(self):
        self.connection.close()

    def make(self, industry_code):
        """
        根据行业代码构造表达式
        :param industry_code: 行业代码
        :return:
        """
        # 获取行业关键字
        keywords = self.get_industry_keywords(industry_code)
        # 获取行业对应的ipc code
        ipc_codes = self.get_ipc_codes_of_industry(industry_code)
        # 生成表达式
        title = 'TI = ( %s )' % '+'.join(keywords)
        abstract = 'AB = ( %s )' % '+'.join(keywords)
        ipc_codes = ["'%s'" % code for code in ipc_codes]
        ipc_code = 'CLC = (%s)' % '+'.join(ipc_codes)
        txt = '({title} OR {abstract}) AND {ipc_code}'.format(title=title, abstract=abstract, ipc_code=ipc_code)
        return txt

    def make_and_save(self, industry_code):
        txt = self.make(industry_code)
        json_data = [{'expertvalue': txt}]
        # 文件路径
        pending = os.path.join(PAGE_DIR, 'pending')
        if not os.path.exists(pending):
            os.makedirs(pending)
        filename = os.path.join(pending, '{}.json'.format(industry_code))
        # 写入到文件
        with open(filename, 'w', encoding='utf-8') as fp:
            json.dump(json_data, fp, ensure_ascii=False, indent=2)

    def get_ipc_codes_of_industry(self, industry_code):
        sql = """
        select ipc_code from industry_ipc
        where industry_code=?
        """
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            data = select(cursor, sql, industry_code)
            results = [datum['ipc_code'] for datum in data]
            return results

    def get_industry_keywords(self, industry_code):
        """根据行业代码获取该行业的关键字/产品/工艺"""
        sql = """select keywords from industry where code like '%s%%%%' """  # 由于db.py内部有一个转义，所以需要4个%
        sql = sql % industry_code
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            datum = select_one(cursor, sql)
            keywords = datum['keywords'].split('；')
            return keywords


if __name__ == '__main__':
    search = CNKIExpertSearch()
    search.make_and_save('0111')
