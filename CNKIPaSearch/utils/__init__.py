import logging
from datetime import datetime


def date2str(date=None, year=None):
    if date is None:
        date = datetime(year=year, month=1, day=1)
    date_string = date.strftime('%Y-%m-%d')
    return date_string


def str2date(text):
    date = datetime.strptime(text, '%Y-%m-%d')
    return date


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


def _insert(cursor, sql, insertMany, *args):
    """
    insert语句
    :param sql: SQL语句 内部变量使用?
    :param insertMany: 是否要插入多行
    :param args: SQL语句中要使用的变量
    :return: 返回插入的结果 插入失败则返回-1
    """
    logging.info('SQL: %s %s' % (sql, args if len(args) > 0 else ""))
    sql = sql.replace('?', '%s')
    # 利用本身的 execute 函数的特性，传入两个参数：sql语句与tuple类型的参数，以避免sql注入
    if insertMany:
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


def _delete(cursor, sql, *args):
    """
     delete语句
    :param cursor: 游标
    :param sql: SQL语句 内部变量使用?
    :param args: SQL语句中要使用的变量
    :return: 返回
    """
    logging.info('SQL: %s %s' % (sql, args if len(args) > 0 else ""))
    sql = sql.replace('?', '%s')
    # 利用本身的 execute 函数的特性，传入两个参数：sql语句与tuple类型的参数，以避免sql注入
    cursor.execute(sql, args)
    # 获取影响的行
    row_count = cursor.rowcount
    return row_count


def delete(cursor, sql, *args):
    return _delete(cursor, sql, *args)
