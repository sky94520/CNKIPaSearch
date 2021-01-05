# --coding:UTF-8--
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess

custom_settings = {
    'page': {
        'DOWNLOADER_MIDDLEWARES': {
            'CNKIPaSearch.middlewares.GetFromLocalityMiddleware': 543,
            'CNKIPaSearch.middlewares.RetryOrErrorMiddleware': 550,
            'CNKIPaSearch.middlewares.ProxyMiddleware': 843,
            'CNKIPaSearch.middlewares.CookieMiddleware': 844,
        },
        'ITEM_PIPELINES': {
            'CNKIPaSearch.pipelines.SaveSearchJsonPipeline': 300,
            'CNKIPaSearch.pipelines.SaveSearchHtmlPipeline': 301,
        }
    },
    'number': {
        'DOWNLOADER_MIDDLEWARES': {
            'CNKIPaSearch.middlewares.RetryOrErrorMiddleware': 550,
            'CNKIPaSearch.middlewares.ProxyMiddleware': 843,
            'CNKIPaSearch.middlewares.CookieMiddleware': 844,
        },
        'ITEM_PIPELINES': {
            'CNKIPaSearch.pipelines.SaveNumberCsvPipeline': 300,
        }
    }
}


def start_spider(crawl_strategy='page'):
    """
    默认使用page方式进行爬取
    :param crawl_strategy: page | number
    :return:
    """
    project_settings = get_project_settings()
    settings = dict(project_settings.copy())
    settings.update(custom_settings[crawl_strategy])
    # 合并配置
    process = CrawlerProcess(settings)
    # 爬取使用的spider名称
    arguments = {'crawl_strategy': crawl_strategy}
    process.crawl(crawler_or_spidercls='page', **arguments)
    process.start()


if __name__ == '__main__':
    start_spider('page')
