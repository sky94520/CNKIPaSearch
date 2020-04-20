from datetime import datetime, timedelta


class ThesisLevel(object):
    """
    专利类型 发明公开 外观设计和实用新型 并未用到
    TODO: 必须是字符串
    """
    INVENT_PATENT = 1
    DESIGN_PATENT = 2
    UTILITY_PATENT = 3


class BaseConfig(object):
    @staticmethod
    def _get_now_gmt_time():
        """
        获取当前的中国标准时间，主要用于赋值给form data
        :return: 当前的时间字符串
        """
        GMT_FORMAT = '%a %b %d %Y %H:%M:%S GMT+0800'
        now = datetime.utcnow() + timedelta(hours=8)
        text = '%s (中国标准时间)' % now.strftime(GMT_FORMAT)

        return text

    @staticmethod
    def _update_thesis_level(params, **kwargs):
        """专利类型"""
        if 'thesis_level' in kwargs:
            params['@thesislevel'] = '专利类别=%s' % kwargs['thesis_level']

    @staticmethod
    def is_matching(datum):
        """根据数据中带有的类型，判断是否使用本类"""
        return False


class ApplicantConfig(BaseConfig):
    """申请人配置"""

    @staticmethod
    def get_params(applicant):
        params = {
            "action": "",
            "NaviCode": "*",
            "ua": "1.21",
            "isinEn": "0",
            "PageName": "ASP.brief_result_aspx",
            "DbPrefix": "SCPD",
            "DbCatalog": "中国专利数据库",
            "ConfigFile": "SCPD.xml",
            "db_opt": "SCOD",
            "db_value": "中国专利数据库",
            "txt_1_sel": "SQR",
            "txt_1_value1": applicant,
            "txt_1_relation": "#CNKI_AND",
            "txt_1_special1": "=",
            "his": 0,
            "__": BaseConfig._get_now_gmt_time()
        }
        return params

    @staticmethod
    def is_matching(datum):
        return 'applicant' in datum and len(datum) == 1


class ApplicantAndDateConfig(BaseConfig):
    """申请人 专利公开日期 配置"""

    @staticmethod
    def get_params(applicant, from_date, to_date):
        params = {
            "action": "",
            "NaviCode": "*",
            "ua": "1.21",
            "isinEn": "0",
            "PageName": "ASP.brief_result_aspx",
            "DbPrefix": "SCPD",
            "DbCatalog": "中国专利数据库",
            "ConfigFile": "SCPD.xml",
            "db_opt": "SCOD",
            "db_value": "中国专利数据库",
            "date_gkr_from": from_date,
            "date_gkr_to": to_date,
            "txt_1_sel": "SQR",
            "txt_1_value1": applicant,
            "txt_1_relation": "#CNKI_AND",
            "txt_1_special1": "=",
            "his": 0,
            "__": BaseConfig._get_now_gmt_time()
        }
        return params

    @staticmethod
    def is_matching(datum):
        keys = ['applicant', 'from_date', 'to_date']
        return all([key in datum for key in keys])


class ApplicantsAndDateConfig(BaseConfig):
    """申请人 公开日期"""

    @staticmethod
    def get_params(applicants, from_date, to_date):
        """
        :param applicants: 申请人数组
        :param from_date: 公开日开始日期 格式 2019-01-01
        :param to_date: 公开日结束日期 格式 2020-01-01
        :return:
        """
        params = {
            "action": "",
            "NaviCode": "*",
            "ua": "1.21",
            "isinEn": "0",
            "PageName": "ASP.brief_result_aspx",
            "DbPrefix": "SCPD",
            "DbCatalog": "中国专利数据库",
            "ConfigFile": "SCPD.xml",
            "db_opt": "SCOD",
            "date_gkr_from": from_date,
            "date_gkr_to": to_date,
            "db_value": "中国专利数据库",
            "his": 0,
            "__": BaseConfig._get_now_gmt_time()
        }
        for idx, applicant in enumerate(applicants, 1):
            params.update({
                'txt_%d_sel' % idx: "SQR",
                "txt_%d_value1" % idx: applicant,
                "txt_%d_relation" % idx: "#CNKI_OR",
                "txt_%d_special1" % idx: "=",
            })
            if idx > 1:
                params["txt_%d_logical" % (idx + 1)] = "or"
        return params

    @staticmethod
    def is_matching(datum):
        keys = ['applicants', 'from_date', 'to_date']
        return all([key in datum for key in keys])


class MainClsNumberConfig(BaseConfig):
    """主分类号配置 txt_1_value1设置"""

    @staticmethod
    def get_params(main_cls_number, **kwargs):
        params = {
            "action": "",
            "NaviCode": "*",
            "ua": "1.21",
            "isinEn": "0",
            "PageName": "ASP.brief_result_aspx",
            "DbPrefix": "SCPD",
            "DbCatalog": "中国专利数据库",
            "ConfigFile": "SCPD.xml",
            "db_opt": "SCOD",
            "db_value": "中国专利数据库",
            "txt_1_sel": "CLZ$=|?",
            "txt_1_value1": main_cls_number,
            "txt_1_relation": "#CNKI_AND",
            "txt_1_special1": "=",
            "his": 0,
            "__": BaseConfig._get_now_gmt_time()
        }
        BaseConfig._update_thesis_level(params, **kwargs)
        return params

    @staticmethod
    def is_matching(datum):
        return 'main_cls_number' in datum


class KeyWordConfig(BaseConfig):
    @staticmethod
    def get_params(keyword):
        params = {
            "action": "",
            "NaviCode": "*",
            "ua": "1.21",
            "isinEn": "0",
            "PageName": "ASP.brief_result_aspx",
            "DbPrefix": "SCPD",
            "DbCatalog": "中国专利数据库",
            "ConfigFile": "SCPD.xml",
            "db_opt": "SCOD",
            "db_value": "中国专利数据库",
            "txt_1_sel": "SU$%=|",
            "txt_1_value1": keyword,
            "txt_1_relation": "#CNKI_AND",
            "txt_1_special1": "=",
            "his": 0,
            "__": BaseConfig._get_now_gmt_time()
        }
        return params

    @staticmethod
    def is_matching(datum):
        return 'keyword' in datum


def get_config_class(datum):
    """工厂函数，用于通过数据的格式来选择配置"""
    configurations = [ApplicantAndDateConfig, ApplicantConfig, KeyWordConfig, MainClsNumberConfig]
    for config_class in configurations:
        if config_class.is_matching(datum):
            return config_class
