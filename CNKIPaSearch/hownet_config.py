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


configurations = {'ApplicantConfig': ApplicantConfig, 'MainClsNumberConfig': MainClsNumberConfig}