# --coding:UTF-8--
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import defer, reactor
from CNKIPaSearch.spiders.page import PageSpider
from CNKIPaSearch.spiders.detail import DetailSpider


configure_logging()
project_settings = get_project_settings()
settings = dict(project_settings.copy())
runner = CrawlerRunner(settings)


@defer.inlineCallbacks
def crawl():
    yield runner.crawl(PageSpider)
    yield runner.crawl(DetailSpider)
    reactor.stop()


if __name__ == '__main__':
    # 爬取 先获取页面，然后获取具体信息
    crawl()
    reactor.run()
