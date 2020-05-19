# --coding:UTF-8--
import os
import json
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import defer, reactor
from CNKIPaSearch.spiders.page import PageSpider
from CNKIPaSearch.spiders.detail import DetailSpider
from CNKIPaSearch.params.TurnPersistParam import TurnPersistParam


configure_logging()
project_settings = get_project_settings()
settings = dict(project_settings.copy())
runner = CrawlerRunner(settings)
basedir = os.path.realpath(os.path.dirname(__name__))


@defer.inlineCallbacks
def crawl():
    yield runner.crawl(PageSpider)
    yield runner.crawl(DetailSpider)
    # TODO:持久化 在容器中会存在问题
    param = TurnPersistParam(basedir)
    while len(param.request_queue) > 0:
        output = os.path.join('files', 'page_pending')
        if not os.path.exists(output):
            os.makedirs(output)
        # TODO:获取队列首部数据 dict
        datum = param.pop()
        output_file = os.path.join(output, '%s.json' % list(datum.values())[0])
        with open(output_file, 'w', encoding='utf-8') as fp:
            json.dump([datum], fp, ensure_ascii=False, indent=2)
        # 分别调用两个爬虫
        yield runner.crawl(PageSpider)
        yield runner.crawl(DetailSpider)
    reactor.stop()


if __name__ == '__main__':
    # 爬取 先获取页面，然后获取具体信息
    crawl()
    reactor.run()
