# --coding:UTF-8--
import os
import re
import json
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import defer, reactor

from CNKIPaSearch.settings import PAGE_DIR
from CNKIPaSearch.spiders import PageSpider, DetailSpider, StatusSpider
from CNKIPaSearch.params.TurnPersistParam import TurnPersistParam


configure_logging()
project_settings = get_project_settings()
settings = dict(project_settings.copy())
runner = CrawlerRunner(settings)
basedir = os.path.realpath(os.path.dirname(__name__))


def generate_dirname(datum):
    """根据字典生成一个文件名"""
    # 数据中含有存在键dirname，那么就以对应的值作为文件名
    if 'dirname' in datum:
        dirname = datum['dirname']
    else:
        # 以第一个作为文件名， 其他作为另外的文件名
        values = list(datum.values())
        # 必定存在一个键值对
        dirname = re.sub('/', '-', values[0])
        if len(values) > 1:
            dirname = os.path.join(dirname, ','.join(values[1:]))
    return dirname


@defer.inlineCallbacks
def crawl(basedir=basedir):
    yield runner.crawl(PageSpider)
    yield runner.crawl(DetailSpider)
    yield runner.crawl(StatusSpider)
    # TODO:持久化 在容器中会存在问题
    param = TurnPersistParam(basedir)
    while len(param.request_queue) > 0:
        # 拆分每个请求，调用page爬虫进行爬取
        page_pending_dir = os.path.join(PAGE_DIR, 'pending')
        if not os.path.exists(page_pending_dir):
            os.makedirs(page_pending_dir)
        # TODO:获取队列首部数据 dict
        datum = param.pop()
        dirname = generate_dirname(datum)
        output_file = os.path.join(page_pending_dir, '%s.json' % dirname)
        with open(output_file, 'w', encoding='utf-8') as fp:
            json.dump([datum], fp, ensure_ascii=False, indent=2)
        # 分别调用两个爬虫
        yield runner.crawl(PageSpider)
        yield runner.crawl(DetailSpider)
        yield runner.crawl(StatusSpider)
    reactor.stop()


if __name__ == '__main__':
    # 爬取 先获取页面，然后获取具体信息
    crawl()
    reactor.run()
    print('run_page_and_detail end.')
