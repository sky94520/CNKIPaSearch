"""
该类获取战略性新兴产业对应的IPC和关键字
根据IPC的层级规则，部、大类是功能划分；小类，大组是事物或事物的集合划分。因此统一使用小类
"""
import logging
import pymysql

from config import MYSQL_CONFIG
from CNKIPaSearch.utils import select, select_one


class StrategicEmergingIndustry(object):
    """根据战略性新兴产业-国民经济行业-IPC 获取对应的IPC"""
    def __init__(self, sei_code):
        self.sei_code = sei_code
        self.logger = logging.getLogger('IPCGetter')
        self.connection = pymysql.connect(**MYSQL_CONFIG)

    def __del__(self):
        self.connection.close()

    def get_total_ipc_codes(self):
        """获取战略性新兴产业对应的ipc"""
        results = set()
        industries = self.get_industries_of_sei()
        for industry in industries:
            industry_code, is_full_equivalence = industry['industry_code'], industry['is_full_equivalence']
            data = self.get_ipc_codes_of_industry(industry_code, is_full_equivalence)
            results = results.union(data)
        return results

    def get_keywords_of_industry(self, industry_code):
        """
        获取战略性新兴产业-国民经济行业 对应的关键字
        :param industry_code: 国民经济行业代码
        :return: list() 关键字
        """
        sql = """
        SELECT keywords FROM `sei_industry` where sei_code=? and industry_code=?
        """
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            datum = select_one(cursor, sql, self.sei_code, industry_code)
            if datum['keywords']:
                keywords = datum['keywords'].split('|')
                keywords = [keyword.strip() for keyword in keywords]
                return keywords
            else:
                return []

    def get_ipc_codes_of_industry(self, industry_code, is_full_equivalence):
        """
        获取该战略性新兴产业-国民经济行业对应的IPC codes
        :param industry_code: 国民经济行业代码
        :param is_full_equivalence: industry_code是否完全属于该战略性新兴产业
        :return: set (ipc, is_full_equivalence)
        """
        results = set()
        data = self._get_ipc_codes_of_sei(industry_code)
        ipc_codes = self.extend_ipc_codes(data, is_full_equivalence)
        for code, is_full_equivalence in ipc_codes.items():
            results.add((code, is_full_equivalence))
        return results

    def extend_ipc_codes(self, ipc_codes, is_full_equivalence):
        """把IPC代码定位到大组和小组"""
        results = {}
        sub_classes, groups = {}, {}
        for ipc in ipc_codes:
            code, depth = ipc['code'], ipc['depth']
            is_full_equivalence = is_full_equivalence and ipc['is_full_equivalence']
            # 小类=>大组
            if depth == 2:
                sub_classes[code] = is_full_equivalence
            # 大组 直接添加
            elif depth == 3:
                groups[code] = is_full_equivalence
                results[code] = is_full_equivalence
            else:
                results[code] = is_full_equivalence
        # 对于小类，先获取大组
        if sub_classes:
            temp = self._get_ipc_code_by_parent_codes(sub_classes)
            for code, is_full_equivalence in temp.items():
                groups[code] = is_full_equivalence
        return results

    def _get_ipc_codes_of_sei(self, industry_code):
        """根据战略性新兴产业获取对应的ipc代码(大类、大组和小组)"""
        sql = """
        select industry.code industry_code,ipc.code,ipc.depth,industry_ipc.is_full_equivalence from sei_industry
        join industry on sei_industry.industry_code=industry.code
        join industry_ipc on industry.`code`=industry_ipc.industry_code
        join ipc on ipc.code=industry_ipc.ipc_code
        where sei_industry.sei_code=? and industry.code=?
        """
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            data = select(cursor, sql, self.sei_code, industry_code)
        return data

    def _get_ipc_code_by_parent_codes(self, codes):
        """通过parent_code=ipc_code获取子ipc code"""
        if not codes:
            return
        sql = """
        select code, parent_code from ipc where parent_code in (%s)
        """
        words = ['?'] * len(codes.keys())
        sql = sql % ','.join(words)
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            data = select(cursor, sql, *codes.keys())
        results = {datum['code']: codes[datum['parent_code']] for datum in data}
        return results

    def get_industries_of_sei(self):
        sql = """
        select sei_code,industry_code,is_full_equivalence from sei_industry
        where sei_code=?
        """
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            data = select(cursor, sql, self.sei_code)
        return data

    def get_total_sei_codes(self):
        sql = """
        SELECT DISTINCT code FROM `strategic_emerging_industry` sei
        join sei_industry on sei.code=sei_industry.sei_code
        """
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            data = select(cursor, sql)
        results = [datum['code'] for datum in data]
        return results

    def get_not_enough_tagging_sei_codes(self, threshold):
        """
        从数据库获取少于threshold专利数量的战略性新兴产业
        :param threshold:
        :return:
        """
        sql = """
        select sei_code from sei_patent
        join strategic_emerging_industry sei on sei.code=sei_code
        where sei.is_exist_patent=1 and LEFT(sei.code,1) <> '3'
        GROUP BY sei_code HAVING count(*) < ?
        union
        select sei2.code from strategic_emerging_industry sei2 where sei2.parent_code in 
        (
        select sei_code count from sei_patent
        join strategic_emerging_industry sei on sei.code=sei_code
        where sei.is_exist_patent=1 and LEFT(sei.code,1) = '3'
        GROUP BY sei_code HAVING count(*) < ?)
        """
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            data = select(cursor, sql,threshold, threshold)
            sei_codes = [datum['sei_code'] for datum in data]
            sql = """
            select sei_code, industry_code from sei_industry where sei_code in (%s)
            """
            words = ['?'] * len(sei_codes)
            sql = sql % ','.join(words)
            data = select(cursor, sql, *sei_codes)
            return data
