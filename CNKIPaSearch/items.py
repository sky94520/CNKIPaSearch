# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SearchItem(scrapy.Item):
    KEYS = ['dbcode', 'dbname', 'filename']
    # define the fields for your item here like:
    array = scrapy.Field()
    response = scrapy.Field()


class NumberItem(scrapy.Item):
    name = scrapy.Field()
    number = scrapy.Field()


class StatusItem(scrapy.Item):
    KEYS = ['date', 'status', 'information']
    # define the fields for your item here like:
    array = scrapy.Field()
    response = scrapy.Field()
    path = scrapy.Field()
    publication_number = scrapy.Field()


class PatentItem(scrapy.Item):
    # TODO:数据库集合名称 发明授权专利
    collection = 'invention_patent'
    mapping = {
        '申请号': 'application_number', '申请日': 'application_date',
        '公开号': 'publication_number', '公开日': 'publication_date',
        '申请人': 'applicant', '地址': 'address',
        '共同申请人': 'joint_applicant',
        '发明人': 'inventor',
        '专利代理机构': 'agency', '代理人': 'agent',
        '国省代码': 'code',
        '摘要': 'summary',
        '主权项': 'sovereignty',
        '页数': 'page_number',
        '主分类号': 'main_cls_number',
        '专利分类号': 'patent_cls_number'
    }
    # 保存response
    response = scrapy.Field()
    path = scrapy.Field()
    # 该url的来源文件
    source = scrapy.Field()
    # 专利名
    title = scrapy.Field()
    # 申请号
    application_number = scrapy.Field()
    # 申请日
    application_date = scrapy.Field()
    # 公开号
    publication_number = scrapy.Field()
    # 公开日
    publication_date = scrapy.Field()
    # 申请人
    applicant = scrapy.Field()
    # 地址
    address = scrapy.Field()
    # 共同申请人
    joint_applicant = scrapy.Field()
    # 发明人
    inventor = scrapy.Field()
    # 代理机构
    agency = scrapy.Field()
    # 代理人
    agent = scrapy.Field()
    # 国省代码
    code = scrapy.Field()
    # 摘要
    summary = scrapy.Field()
    # 主权项
    sovereignty = scrapy.Field()
    # 页数
    page_number = scrapy.Field()
    # 主分类号
    main_cls_number = scrapy.Field()
    # 专利分类号
    patent_cls_number = scrapy.Field()
