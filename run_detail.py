# --coding:UTF-8--
import os
# from dotenv import load_dotenv
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess


def run():
    # 加载.env配置文件
    # load_dotenv()
    # 爬取使用的spider名称
    spider_name = 'detail'
    project_settings = get_project_settings()
    settings = dict(project_settings.copy())
    # 合并配置
    process = CrawlerProcess(settings)
    # 启动爬虫
    process.crawl(spider_name)
    process.start()


if __name__ == '__main__':
    run()
