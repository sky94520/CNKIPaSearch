# --coding:UTF-8--
import os
import json
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import defer, reactor
from CNKIPaSearch.spiders.page import PageSpider
from CNKIPaSearch.spiders.detail import DetailSpider
from CNKIPaSearch.utils import date2str


configure_logging()
project_settings = get_project_settings()
settings = dict(project_settings.copy())
runner = CrawlerRunner(settings)


@defer.inlineCallbacks
def crawl():
    applicants = ['昆山国宝过滤机有限公司', '苏州藤堂精密机械有限公司']
    for applicant in applicants:
        json_data = [{"applicant": applicant}]
        output = os.path.join('files', 'pending')
        if not os.path.exists(output):
            os.makedirs(output)
        output_file = os.path.join(output, '%s.json' % applicant)
        with open(output_file, 'w', encoding='utf-8') as fp:
            json.dump(json_data, fp, ensure_ascii=False, indent=2)
        yield runner.crawl(PageSpider)
        yield runner.crawl(DetailSpider)
    reactor.stop()


if __name__ == '__main__':
    # 爬取 先获取页面，然后获取具体信息
    crawl()
    reactor.run()
