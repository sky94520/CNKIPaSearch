import logging


def _select(cursor, sql, first, *args):
    """
    select语句
    :param sql: SQL语句 内部变量使用?
    :param first: 是否只获取一个
    :param args: SQL语句中要使用的变量
    :return: 返回查询的结果
    """
    logging.info('SQL: %s %s' % (sql, args if len(args) > 0 else ""))
    sql = sql.replace('?', '%s')
    # 利用本身的 execute 函数的特性，传入两个参数：sql语句与tuple类型的参数，以避免sql注入
    cursor.execute(sql, args)
    if first:
        result = cursor.fetchone()
        return result
    else:
        results = cursor.fetchall()
        return results


def select_one(cursor, sql, *args):
    return _select(cursor, sql, True, *args)


def select(cursor, sql, *args):
    return _select(cursor, sql, False, *args)


def _insert(cursor, sql, insert_many, *args):
    """
    insert语句
    :param sql: SQL语句 内部变量使用?
    :param insert_many: 是否要插入多行
    :param args: SQL语句中要使用的变量
    :return: 返回插入的结果 插入失败则返回-1
    """
    logging.info('SQL: %s %s' % (sql, args if len(args) > 0 else ""))
    sql = sql.replace('?', '%s')
    # 利用本身的 execute 函数的特性，传入两个参数：sql语句与tuple类型的参数，以避免sql注入
    if insert_many:
        # 插入多行
        cursor.executemany(sql, args)
    else:
        cursor.execute(sql, args)
    # 返回最后插入行的主键ID
    return cursor.lastrowid


def insert(cursor, sql, *args):
    return _insert(cursor, sql, False, *args)


def insert_many(cursor, sql, *args):
    return _insert(cursor, sql, True, *args)


def test(cursor, item, success_callback):
    return


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
        success_callback(item)
        return
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
    insert_many(cursor, insert_app_patent_sql, *[(applicant_id, patent_id) for applicant_id in applicant_id_mapping.values()])
    # 发明人
    insert_inventor_sql = """insert into inventor(name,patent_id) values(?,?)"""
    insert_many(cursor, insert_inventor_sql, *[(inventor, patent_id) for inventor in inventors])
    # 插入专利文本
    insert_text_sql = """insert into patent_text(summary,sovereignty, patent_id) values(?,?,?)"""
    insert(cursor, insert_text_sql, summary, sovereignty, patent_id)

    success_callback(item)

