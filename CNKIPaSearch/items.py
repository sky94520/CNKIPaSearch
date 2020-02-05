# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PatentItem(scrapy.Item):
    KEYS = ['dbcode', 'dbname', 'filename']
    # define the fields for your item here like:
    # title = scrapy.Field()
    # dbcode = scrapy.Field()
    # dbname = scrapy.Field()
    # filename = scrapy.Field()
    array = scrapy.Field()
    response = scrapy.Field()
