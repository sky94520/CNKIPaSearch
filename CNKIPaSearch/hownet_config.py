from datetime import datetime, timedelta


class ThesisLevel(object):
    """
    专利类型 发明公开、外观设计、实用新型和发明授权
    TODO: 必须是字符串 目前并未用到，只是起到提醒作用`
    """
    INVENT_PATENT = 1
    DESIGN_PATENT = 2
    UTILITY_PATENT = 3
    GRANTED_PATENT = 4


# 公开日
FROM_DATE_KEY = 'date_gkr_from'
TO_DATE_KEY = 'date_gkr_to'
# 申请日
FROM_PUBLISH_DATE_KEY = 'publishdate_from'
TO_PUBLISH_DATE_KEY = 'publishdate_to'

CONDITIONS = {
    'applicant': 'SQR',
    'keyword': 'SU$%=|',
    'main_cls_number': 'CLZ$=|?'
}


class BaseConfig(object):
    """通过该类设置搜索条件"""
    @staticmethod
    def _get_condition(idx, condition, value):
        result = {
            'txt_%d_sel' % idx: condition,
            "txt_%d_value1" % idx: value,
            "txt_%d_relation" % idx: "#CNKI_OR",
            "txt_%d_special1" % idx: "=",
        }
        return result

    @staticmethod
    def get_config_params(datum):
        params = BaseConfig._get_base_params()
        """工厂函数，用于通过数据的格式来选择配置"""
        # 专业检索
        if 'expertvalue' in datum:
            params['expertvalue'] = datum['expertvalue']
        else:
            BaseConfig._advanced_search(params, datum)
        # ---公开日---
        if FROM_DATE_KEY in datum:
            params[FROM_DATE_KEY] = datum[FROM_DATE_KEY]
        if TO_DATE_KEY in datum:
            params[TO_DATE_KEY] = datum[TO_DATE_KEY]
        # --- 申请日---
        if FROM_PUBLISH_DATE_KEY in datum:
            params[FROM_PUBLISH_DATE_KEY] = datum[FROM_DATE_KEY]
        if TO_PUBLISH_DATE_KEY in datum:
            params[TO_PUBLISH_DATE_KEY] = datum[TO_PUBLISH_DATE_KEY]
        # 专利类型
        if 'thesis_level' in datum:
            BaseConfig._update_thesis_level(params, **datum)
        return params

    @staticmethod
    def _advanced_search(params, datum):
        """知网 高级检索"""
        idx, logical_idx = 1, 1
        for key, value in datum.items():
            if key in CONDITIONS:
                condition = BaseConfig._get_condition(idx, CONDITIONS[key], value)
                params.update(condition)
                idx += 1
            # 或or 与 and
            elif idx > 1:
                params["txt_%d_logical" % idx] = value

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
    def _update_thesis_level(params, **kwargs):
        """专利类型"""
        params['@thesislevel'] = '专利类别=%s' % kwargs['thesis_level']
