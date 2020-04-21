# --coding:UTF-8--
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess


def start_spider(spider_name):
    project_settings = get_project_settings()
    settings = dict(project_settings.copy())
    # 合并配置
    process = CrawlerProcess(settings)
    process.crawl(spider_name)
    process.start()


if __name__ == '__main__':
    # 爬取
    start_spider(spider_name='page')
    start_spider(spider_name='detail')
