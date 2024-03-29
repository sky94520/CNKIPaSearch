# -*- coding: utf-8 -*-

# Scrapy settings for CNKIPaSearch project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import os

BOT_NAME = 'CNKIPaSearch'

SPIDER_MODULES = ['CNKIPaSearch.spiders']
NEWSPIDER_MODULE = 'CNKIPaSearch.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'CNKIPaSearch (+http://www.yourdomain.com)'
# 限制并发请求数量
CONCURRENT_REQUESTS = 4

# Obey robots.txt rules
ROBOTSTXT_OBEY = False
BASEDIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
# page爬虫爬取数据存放路径
PAGE_DIR = os.path.join(BASEDIR, 'files', 'page')
# detail爬虫爬取数据存放路径
DETAIL_DIR = os.path.join(BASEDIR, 'files', 'detail')
STATUS_DIR = os.path.join(BASEDIR, 'files', 'status')
# 最大重试次数
MAX_RETRY_TIMES = 20
# 每个页面的专利个数
PATENT_NUMBER_PER_PAGE = 50
# 知网能爬取的最大个数
MAX_PATENT_NUM = 6000
# 禁止重定向
REDIRECT_ENALBED = False
# 允许出现404 403
HTTPERROR_ALLOWED_CODES = [404, 403, 401, 407, 503]
# 下载限制15秒为延时 默认180s
DOWNLOAD_TIMEOUT = 15
TELNETCONSOLE_USERNAME = 'scrapy'
TELNETCONSOLE_PASSWORD = 'scrapy'
# 默认下载延迟[0.5 * delay, 1.5 * delay] => [0.25, 0.75]
DOWNLOAD_DELAY = 0.5
RANDOMIZE_DOWNLOAD_DELAY = True
# 限制最多response数量
# SCRAPER_SLOT_MAX_ACTIVE_SIZE = 1024*512
# LOG_LEVEL = 'WARNING'

# DOWNLOADER_MIDDLEWARES = {
#     'CNKIPaSearch.middlewares.RetryOrErrorMiddleware': 550,
#     'CNKIPaSearch.middlewares.ProxyMiddleware': 843,
#     'CNKIPaSearch.middlewares.CookieMiddleware': 844,
# }
# # Configure item pipelines
# # See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#     'CNKIPaSearch.pipelines.JsonPipeline': 300,
#     'CNKIPaSearch.pipelines.SavePagePipeline': 301,
# }
