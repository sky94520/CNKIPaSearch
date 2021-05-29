from . import select_one, select, insert_many, insert, delete


def import_patent(cursor, item, success_callback, spider):
    application_number = item['application_number']
    # 通过application_number保证唯一
    is_exist = _get_patent_by_application_number(cursor, application_number)
    if is_exist:
        return success_callback(item, spider)
    # 插入专利 专利文本和专利发明人
    patent_id = _insert_patent(cursor, item)
    # 插入专利和对应的IPC
    _insert_patent_ipc(cursor, patent_id, item['patent_cls_number'])
    # 插入专利和申请人
    _insert_patent_applicants(cursor, patent_id, item['applicant'])
    # 插入成功回调函数
    return success_callback(item, spider)


def _get_patent_by_application_number(cursor, application_number):
    """根据专利申请号，获取专利数据"""
    get_patent_sql = 'select application_number from patent where application_number=?'
    back = select_one(cursor, get_patent_sql, application_number)
    return back


def _get_category_of_patent(application_number):
    """根据专利申请号获取专利的类型 1发明专利 2 实用新型 3外观设计 8PCT发明专利 9PCT实用新型"""
    # 2003年以前专利申请号编号形式（8位数字加上一个小数点,不包含CN） 第3位数字表示专利类型
    # 例如：CN 01 3 31070.4，即该专利是2001年申请的第31070件外观设计专利。
    if len(application_number) < 14:
        category = application_number[4]
    # 2003年以后的专利申请编号形式 申请年号+专利申请种类+申请顺序号+计算机校验位 不算CN 前4位数字表示申请年号，第5位数字表示申请种类
    # CN201630530195.0
    else:
        category = application_number[6]
    return int(category)


def _insert_patent(cursor, item):
    """插入数据到专利表"""
    title = item['title']
    application_number = item['application_number']
    publication_number = item['publication_number'] if 'publication_number' in item else None
    application_date = item['application_date']
    publication_date = item['publication_date'] if 'publication_date' in item else None
    main_cls_number = item['main_cls_number']
    category = _get_category_of_patent(application_number)
    # 插入专利数据
    insert_sql = """insert into patent(title,application_number,publication_number,publication_date,
    application_date,main_cls_number, category) values(?,?,?,?,?,?,?)"""
    patent_id = insert(cursor, insert_sql, title, application_number, publication_number, publication_date,
                       application_date, main_cls_number, category)
    # 专利-发明人
    inventors = item['inventor']
    insert_inventor_sql = """insert into inventor(name,patent_id) values(?,?)"""
    insert_many(cursor, insert_inventor_sql, *[(inventor, patent_id) for inventor in inventors])
    # 专利-专利文本
    address = item['address']
    area_code = item['code']
    summary = item['summary']
    sovereignty = item['sovereignty']
    insert_text_sql = """
    insert into patent_text(title,summary,sovereignty, address, area_code, patent_id, application_number)
     values(?,?,?,?,?,?,?)
     """
    insert(cursor, insert_text_sql, title, summary, sovereignty, address, area_code, patent_id, application_number)
    return patent_id


def _insert_patent_ipc(cursor, patent_id, cls_numbers):
    """插入专利的ipc"""
    # sql = """select code from ipc where code in (%s)"""
    # words = ['?'] * len(cls_numbers)
    # sql = sql % ','.join(words)
    # exist_cls_numbers = select(cursor, sql, *cls_numbers)
    # 插入ipc和专利对应的表中
    insert_patent_ipc = "insert into patent_ipc(patent_id,ipc_code) values(?,?)"
    insert_many(cursor, insert_patent_ipc, *[(patent_id, cls_number) for cls_number in cls_numbers])


def _insert_patent_applicants(cursor, patent_id, applicants):
    """插入申请人、专利和申请人的对应表"""
    # 查询申请人是否存在
    select_applicant_sql = """select * from applicant where name in ({})""".format(','.join(['?'] * len(applicants)))
    applicant_results = select(cursor, select_applicant_sql, *applicants)
    applicant_id_mapping = {applicant['name']: applicant['id'] for applicant in applicant_results}
    insert_applicant_sql = """insert into applicant(name) values(?)"""
    for applicant in applicants:
        if applicant not in applicant_id_mapping:
            applicant_id = insert(cursor, insert_applicant_sql, applicant)
            applicant_id_mapping[applicant] = applicant_id
    # 插入申请人-专利
    insert_app_patent_sql = """insert into applicant_patent(applicant_id, patent_id) values(?,?)"""
    insert_many(cursor, insert_app_patent_sql,
                *[(applicant_id, patent_id) for applicant_id in applicant_id_mapping.values()])
