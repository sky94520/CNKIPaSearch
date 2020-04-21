from datetime import datetime, timedelta


class ThesisLevel(object):
    """
    专利类型 发明公开 外观设计和实用新型 并未用到
    TODO: 必须是字符串
    """
    INVENT_PATENT = 1
    DESIGN_PATENT = 2
    UTILITY_PATENT = 3


FROM_DATE_KEY = 'date_gkr_from'
TO_DATE_KEY = 'date_gkr_to'


class BaseConfig(object):

    @staticmethod
    def get_config_params(datum):
        params = BaseConfig._get_base_params()
        """工厂函数，用于通过数据的格式来选择配置"""
        # 互斥
        if 'applicant' in datum:
            BaseConfig._set_applicant(params, **datum)
        elif 'applicants' in datum:
            BaseConfig._set_applicants(params, **datum)
        elif 'keyword' in datum:
            BaseConfig._set_keyword(params, **datum)
        elif 'main_cls_number' in datum:
            BaseConfig._set_main_cls_number(params, **datum)

        # 公开日
        if FROM_DATE_KEY in datum and TO_DATE_KEY in datum:
            BaseConfig._update_gkr(params, **datum)
        # 专利类型
        if 'thesis_level' in datum:
            BaseConfig._update_thesis_level(params, **datum)
        return params

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
    def _get_base_params():
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
            "his": 0,
            "__": BaseConfig._get_now_gmt_time()
        }
        return params

    @staticmethod
    def _update_gkr(params, **kwargs):
        params[FROM_DATE_KEY] = kwargs[FROM_DATE_KEY]
        params[TO_DATE_KEY] = kwargs[TO_DATE_KEY]

    @staticmethod
    def _update_thesis_level(params, **kwargs):
        """专利类型"""
        params['@thesislevel'] = '专利类别=%s' % kwargs['thesis_level']

    @staticmethod
    def _set_applicant(params, **kwargs):
        datum = {
            "txt_1_sel": "SQR",
            "txt_1_value1": kwargs['applicant'],
            "txt_1_relation": "#CNKI_AND",
            "txt_1_special1": "=",
        }
        params.update(datum)

    @staticmethod
    def _set_applicants(params, **kwargs):
        applicants = kwargs['applicants']
        for idx, applicant in enumerate(applicants, 1):
            params.update({
                'txt_%d_sel' % idx: "SQR",
                "txt_%d_value1" % idx: applicant,
                "txt_%d_relation" % idx: "#CNKI_OR",
                "txt_%d_special1" % idx: "=",
            })
            if idx > 1:
                params["txt_%d_logical" % (idx + 1)] = "or"

    @staticmethod
    def _set_keyword(params, **kwargs):
        datum = {
            "txt_1_sel": "SU$%=|",
            "txt_1_value1": kwargs['keyword'],
            "txt_1_relation": "#CNKI_AND",
            "txt_1_special1": "=",
        }
        params.update(datum)

    @staticmethod
    def _set_main_cls_number(params, **kwargs):
        datum = {
            "txt_1_sel": "CLZ$=|?",
            "txt_1_value1": kwargs['main_cls_number'],
            "txt_1_relation": "#CNKI_AND",
            "txt_1_special1": "=",
        }
        params.update(datum)

