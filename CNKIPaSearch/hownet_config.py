from datetime import datetime, timedelta


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


class MainClsNumberConfig(BaseConfig):
    """主分类号配置 txt_1_value1设置 仅仅发明公开"""
    @staticmethod
    def get_params(main_cls_number):
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
            "@thesislevel": "专利类别=1",
            "txt_1_sel": "CLZ$=|?",
            "txt_1_value1": main_cls_number,
            "txt_1_relation": "#CNKI_AND",
            "txt_1_special1": "=",
            "his": 0,
            "__": BaseConfig._get_now_gmt_time()
        }
        return params


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


configurations = {
    'ApplicantConfig': ApplicantConfig,
    'ApplicantAndDateConfig': ApplicantAndDateConfig,
    'ApplicantsAndDateConfig': ApplicantsAndDateConfig,
    'MainClsNumberConfig': MainClsNumberConfig,
    'KeyWordConfig': KeyWordConfig,
}