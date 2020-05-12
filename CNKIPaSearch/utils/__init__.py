from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def date2str(date=None, year=None):
    if date is None:
        date = datetime(year=year, month=1, day=1)
    date_string = date.strftime('%Y-%m-%d')
    return date_string


def str2date(text):
    date = datetime.strptime(text, '%Y-%m-%d')
    return date


# 创建对象的基类:
Base = declarative_base()


# 返回数据库会话
def load_session(uri):
    # 初始化数据库连接:
    engine = create_engine(uri)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session