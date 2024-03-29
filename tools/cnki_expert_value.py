"""
知网专业搜索表达式构造
输入：行业代码
输出：知网专业搜索表达式
"""
import os
import json
from tqdm import tqdm

from CNKIPaSearch.settings import PAGE_DIR
from tools.strategic_emerging_industry import StrategicEmergingIndustry


class CNKIExpertSearch(object):
    """CNKI 专家搜索"""
    def make(self, sei_code, industry_code):
        """
        根据关键字和IPC构造表达式
        :return: 返回构造好的表达式
        """
        getter = StrategicEmergingIndustry(sei_code)
        industries = getter.get_industries_of_sei()
        is_full_equivalence = False
        for industry in industries:
            if industry['industry_code'] == industry_code:
                is_full_equivalence = industry['is_full_equivalence']
        # 获取ipc codes
        ipc_codes = getter.get_ipc_codes_of_industry(industry_code, is_full_equivalence)
        keywords = getter.get_keywords_of_industry(industry_code)
        if not keywords:
            return ''
        else:
            # 对于and 使用(keyword1*keyword2)拼接
            for idx, keyword in enumerate(keywords):
                if 'and' in keyword:
                    keyword = '(%s)' % keyword.replace('and', '*')
                    keywords[idx] = keyword
        # 生成表达式
        title = 'TI = ( %s )' % '+'.join(keywords)
        abstract = 'AB = ( %s )' % '+'.join(keywords)
        ipc_codes = ["'%s'" % code for code, is_full_equivalence in ipc_codes]
        ipc_code = 'CLC = (%s)' % '+'.join(ipc_codes)
        txt = '({title} OR {abstract}) AND {ipc_code}'.format(title=title, abstract=abstract, ipc_code=ipc_code)
        return txt

    def make_and_save(self, sei_code, industry_code):
        txt = self.make(sei_code, industry_code)
        dirname = '{}-{}'.format(sei_code, industry_code)
        json_data = [{'expertvalue': txt, 'dirname': dirname}]
        # 文件路径
        full_filename = os.path.join(PAGE_DIR, 'pending', '{}.json'.format(dirname))
        self.save_json(json_data, full_filename)

    @staticmethod
    def save_json(json_data, full_filename):
        path, filename = os.path.split(full_filename)
        # 文件夹未创建
        if not os.path.exists(path):
            os.makedirs(path)
        # 写入到文件
        with open(full_filename, 'w', encoding='utf-8') as fp:
            json.dump(json_data, fp, ensure_ascii=False, indent=2)


def make_total_sei_codes(patent_count):
    # TODO：在数据库获取少于一定标注数据的
    sei = StrategicEmergingIndustry('1.1.1')
    data = sei.get_not_enough_tagging_sei_codes(300)
    del sei

    search = CNKIExpertSearch()
    json_data = []
    for datum in tqdm(data):
        sei_code, industry_code = datum['sei_code'], datum['industry_code']
        dirname = '{}-{}'.format(sei_code, industry_code)
        # 生成专家表达式
        expert_value = search.make(sei_code, industry_code)
        if len(expert_value) == 0:
            print('{}生成表达式失败'.format(dirname))
            continue
        json_data.append({
            'expertvalue': expert_value,
            'dirname': dirname
        })
    # 文件路径
    full_filename = os.path.join(PAGE_DIR, 'pending', 'sei.json')
    search.save_json(json_data, full_filename)


if __name__ == '__main__':
    sei_code, industry_code = '1.2.1', '3832'
    dirname = '{}-{}'.format(sei_code, industry_code)
    # 生成专家表达式
    search = CNKIExpertSearch()
    expert_value = search.make(sei_code, industry_code)
    print(expert_value)
