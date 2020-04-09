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

