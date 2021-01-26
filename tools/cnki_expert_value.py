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
from tools.ipc_getter import IPCGetter


class CNKIExpertSearch(object):
    """CNKI 专家搜索"""
    def __init__(self):
        self.connection = pymysql.connect(**MYSQL_CONFIG)

    def __del__(self):
        self.connection.close()

    def make(self, keywords, ipc_codes):
        """
        根据行业代码构造表达式
        :return:
        """
        # 获取行业关键字
        # keywords = self.get_industry_keywords(industry_code)
        # 获取行业对应的ipc code
        # ipc_codes = self.get_ipc_codes_of_industry(industry_code)
        # 生成表达式
        title = 'TI = ( %s )' % '+'.join(keywords)
        abstract = 'AB = ( %s )' % '+'.join(keywords)
        ipc_codes = ["'%s'" % code for code, is_full_equivalence in ipc_codes]
        ipc_code = 'CLC = (%s)' % '+'.join(ipc_codes)
        txt = '({title} OR {abstract}) AND {ipc_code}'.format(title=title, abstract=abstract, ipc_code=ipc_code)
        # txt = '({title} OR {abstract})'.format(title=title, abstract=abstract)
        return txt

    def make_and_save(self, sei_code, industry_code):
        getter = IPCGetter(sei_code)
        industries = getter.get_industries_of_sei()
        is_full_equivalence = False
        for industry in industries:
            if industry['industry_code'] == industry_code:
                is_full_equivalence = industry['is_full_equivalence']
        # 获取ipc codes
        ipc_codes = getter.get_ipc_codes_of_industry(industry_code, is_full_equivalence)
        keywords = getter.get_keywords_of_industry(industry_code)

        txt = self.make(keywords, ipc_codes)
        dirname = '{}-{}'.format(sei_code, industry_code)
        json_data = [{'expertvalue': txt, 'dirname': dirname}]
        # 文件路径
        pending = os.path.join(PAGE_DIR, 'pending')
        if not os.path.exists(pending):
            os.makedirs(pending)
        filename = os.path.join(pending, '{}.json'.format(dirname))
        # 写入到文件
        with open(filename, 'w', encoding='utf-8') as fp:
            json.dump(json_data, fp, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    search = CNKIExpertSearch()
    search.make_and_save('3.4.4.5', '3024')
