import logging
from . import select_one, select, insert_many, insert, delete


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
