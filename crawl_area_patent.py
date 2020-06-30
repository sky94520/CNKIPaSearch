# --coding:UTF-8--
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import defer, reactor


configure_logging()
project_settings = get_project_settings()
settings = dict(project_settings.copy())
runner = CrawlerRunner(settings)


@defer.inlineCallbacks
def crawl():
    yield runner.crawl('page')
    yield runner.crawl('detail')
    yield runner.crawl('status')
    reactor.stop()


if __name__ == '__main__':
    # 爬取 先获取页面，然后获取具体信息
    crawl()
    reactor.run()
