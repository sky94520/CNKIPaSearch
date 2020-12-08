# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.


class IdentifyingCodeError(Exception):
    """出现验证码所引发的异常"""

    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


class CrawlStrategyError(Exception):
    """爬取策略出错"""
    def __init__(self, strategy):
        self.strategy = strategy

    def __str__(self):
        return 'invalid crawl strategy, only [page | number], but got %s' % self.strategy


from .page import PageSpider
from .detail import DetailSpider
from .status import StatusSpider