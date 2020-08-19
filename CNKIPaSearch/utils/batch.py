import logging
from . import select_one, select, insert_many, insert, delete


def import_patent(cursor, item, success_callback):
    title = item['title']
    application_number = item['application_number']
    publication_number = item['publication_number']
    application_date = item['application_date']
    publication_date = item['publication_date']
    main_cls_number = item['main_cls_number']
    cls_numbers = item['patent_cls_number']
    applicants = item['applicant']
    inventors = item['inventor']
    summary = item['summary']
    sovereignty = item['sovereignty']
    # 通过application_number保证唯一
    get_patent_sql = 'select publication_number from patent where publication_number=?'
    back = select_one(cursor, get_patent_sql, publication_number)
    if back:
        return success_callback(item)
    # 插入专利数据
    insert_sql = """insert into patent(title,application_number,publication_number,publication_date,
    application_date,main_cls_number) values(?,?,?,?,?,?)"""
    patent_id = insert(cursor, insert_sql, title, application_number, publication_number, publication_date,
                       application_date, main_cls_number)
    # 获取ipc对应的id
    select_ipc_sql = "select * from ipc where code in (%s)" % ','.join(['?'] * len(cls_numbers))
    ipc_list = select(cursor, select_ipc_sql, *cls_numbers)
    # 插入ipc和专利对应的表中
    insert_patent_ipc = "insert into patent_ipc(patent_id,ipc_id) values(?,?)"
    insert_many(cursor, insert_patent_ipc, *[(patent_id, ipc['id']) for ipc in ipc_list])
    # 申请人
    select_applicant_sql = """select * from applicant where name in ({})""".format(','.join(['?'] * len(applicants)))
    applicant_results = select(cursor, select_applicant_sql, *applicants)
    applicant_id_mapping = {applicant['name']: applicant['id'] for applicant in applicant_results}
    insert_applicant_sql = """insert into applicant(name) values(?)"""
    for applicant in applicants:
        if applicant not in applicant_id_mapping:
            applicant_id = insert(cursor, insert_applicant_sql, applicant)
            applicant_id_mapping[applicant] = applicant_id
    # 插入申请人-专利
    insert_app_patent_sql = """
    insert into applicant_patent(applicant_id, patent_id) values(?,?)
    """
    insert_many(cursor, insert_app_patent_sql,
                *[(applicant_id, patent_id) for applicant_id in applicant_id_mapping.values()])
    # 发明人
    insert_inventor_sql = """insert into inventor(name,patent_id) values(?,?)"""
    insert_many(cursor, insert_inventor_sql, *[(inventor, patent_id) for inventor in inventors])
    # 插入专利文本
    insert_text_sql = """insert into patent_text(summary,sovereignty, patent_id) values(?,?,?)"""
    insert(cursor, insert_text_sql, summary, sovereignty, patent_id)

    return success_callback(item)


def import_patent_status(cursor, item):
    """
    插入专利的“状态”到数据库中
    :param cursor: 游标，通过调用该方法增删改查数据
    :param item: {"publication_number": str, "array": [{"date": date, "status": "", "information": ""}]}
    :return:
    """
    publication_number = item['publication_number']
    sql = """select id from patent where publication_number=?"""
    patent = select_one(cursor, sql, publication_number)
    # 不存在对应的patent
    if patent is None:
        logging.warning('patent: publication_number:{} not found in database'.format(publication_number))
        return
    # 判断数据库中的状态数量
    sql = """select count(*) count from patent_status WHERE patent_id=?"""
    result = select_one(cursor, sql, patent['id'])
    if result['count'] >= len(item['array']):
        logging.warning('patent: publication_number:{}\'s status length {} >= {}'.format(publication_number, result['count'], len(item['array'])))
        return
    # 删除原先的数据
    elif result['count'] != 0:
        sql = """delete from patent_status where patent_id=?"""
        rowcount = delete(cursor, sql, patent['id'])
        logging.info('delete patent_status %d, effected row count %d' % (patent['id'], rowcount))
    # 把{status, date, information, patent_id} 存入到buffer
    buffer = []
    for datum in item['array']:
        status = datum['status']
        date = datum['date']
        information = datum['information']
        buffer.append((status, date, information, patent['id']))
    # 插入到数据库中
    insert_sql = """insert into patent_status(status,publication_date, information, patent_id) values(?,?,?,?)"""
    insert_many(cursor, insert_sql, *buffer)
    buffer.clear()
