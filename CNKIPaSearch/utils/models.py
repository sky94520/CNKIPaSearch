import re
from . import Base
from sqlalchemy import Table, Column, Integer, ForeignKey, String, Date, Text
from sqlalchemy.orm import relationship

patent_ipc = Table('patent_ipc',
                   Base.metadata,
                   Column('patent_id', Integer, ForeignKey('patent.id'), primary_key=True),
                   Column('ipc_id', Integer, ForeignKey('ipc.id'), primary_key=True),
                   )

applicant_patent = Table('applicant_patent',
                         Base.metadata,
                         Column('applicant_id', Integer, ForeignKey('applicant.id'), primary_key=True),
                         Column('patent_id', Integer, ForeignKey('patent.id'), primary_key=True)
                         )

teacher_institution = Table('teacher_institution',
                            Base.metadata,
                            Column('teacher_id', Integer, ForeignKey('teacher.id'), primary_key=True),
                            Column('institution_id', Integer, ForeignKey('institution.id'), primary_key=True)
                            )


class Patent(Base):
    """专利"""
    __tablename__ = 'patent'
    id = Column(Integer, primary_key=True)
    title = Column(String(128))
    application_number = Column(String(20))
    publication_number = Column(String(32), unique=True)
    publication_date = Column(Date)
    application_date = Column(Date)
    main_cls_number = Column(String(32))
    # 分类号
    cls_numbers = relationship('IPC', secondary=patent_ipc, back_populates='patents')
    # 申请人
    applicants = relationship('Applicant', secondary=applicant_patent, back_populates='patents')
    # 一个专利有多个发明人
    inventors = relationship('Inventor')
    # 专利文本
    text = relationship('PatentText', uselist=False)

    def __str__(self):
        return self.publication_number

    def __repr__(self):
        return '%s %s' % (self.publication_number, self.title)


class PatentText(Base):
    """
    专门存储专利的文本
    """
    __tablename__ = 'patent_text'
    id = Column(Integer, primary_key=True)
    # title = Column(String(128))
    summary = Column(Text)
    sovereignty = Column(Text)
    patent_id = Column(Integer, ForeignKey('patent.id'))


class Applicant(Base):
    """专利的申请人"""
    __tablename__ = 'applicant'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True)
    # 邮政编码 用来代表所处的位置
    # post_code = Column(String(6))
    # TODO: 更名的情况
    # location = Column(String)
    patents = relationship('Patent', secondary=applicant_patent, back_populates='applicants')


class Inventor(Base):
    __tablename__ = 'inventor'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64))
    # 外键
    patent_id = Column(Integer, ForeignKey('patent.id'))


class IPC(Base):
    """IPC 国家专利分类号"""
    __tablename__ = 'ipc'
    id = Column(Integer, primary_key=True, autoincrement=False)
    code = Column(String(32), unique=True)
    title = Column(Text())
    depth = Column(Integer())
    # 该分类号下的所有专利
    patents = relationship('Patent', secondary=patent_ipc, back_populates='cls_numbers')
    # 邻接列表
    parent_id = Column(Integer, ForeignKey('ipc.id'))
    # 父对象
    parent = relationship('IPC', back_populates='children', remote_side=[id])
    children = relationship('IPC', back_populates='parent', cascade='all')

    def __str__(self):
        return '%s %s' % (self.code, self.title)

    def __repr__(self):
        return '%s %s' % (self.code, self.title)


def batch_import_patent(item, session):
    """
    批量导入专利到数据库
    :param item: item
    :param session:
    :return:
    """
    pattern = re.compile(r'[\r|\n]+')
    # 分批次添加，避免文件夹下太多的文件导致数据库读取问题
    # 获取所有的公开号 查询数据库，仅仅插入那些在数据库中没有的专利
    publication_number = item['publication_number']
    patent = session.query(Patent).filter(Patent.publication_number == publication_number).first()
    # patent = Patent.query.filter(Patent.publication_number == publication_number).first()
    if patent is not None:
        return
    cls_numbers = item['patent_cls_number']
    patent = Patent(title=item['title'],
                    application_number=item['application_number'],
                    publication_number=item['publication_number'],
                    publication_date=item['publication_date'],
                    application_date=item['application_date'],
                    main_cls_number=item['main_cls_number'])
    # 获取ipc的id 然后插入到数据库
    ipc_list = session.query(IPC).filter(IPC.code.in_(cls_numbers))
    # 插入到patent表中，并获取到id
    patent.cls_numbers.extend(ipc_list)
    session.add(patent)
    # 申请人
    for applicant_name in item['applicant']:
        applicant = session.query(Applicant).filter(Applicant.name == applicant_name).first()
        if applicant is None:
            applicant = Applicant(name=applicant_name)
            session.add(applicant)
        applicant.patents.append(patent)
    # 发明人
    for inventor_name in item['inventor']:
        inventor = Inventor(name=inventor_name)
        inventor.patent_id = patent.id
        session.add(inventor)
    # 专利文本
    summary = re.sub(pattern, '', item['summary'])
    sovereignty = re.sub(pattern, '', item['sovereignty'])
    patent_text = PatentText(summary=summary,
                             sovereignty=sovereignty,
                             patent_id=patent.id)
    session.add(patent_text)
    session.commit()
