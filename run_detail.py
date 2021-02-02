# --coding:UTF-8--
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess

custom_settings = {
    'DOWNLOADER_MIDDLEWARES': {
        'CNKIPaSearch.middlewares.GetFromLocalityMiddleware': 543,
        'CNKIPaSearch.middlewares.RetryOrErrorMiddleware': 550,
        'CNKIPaSearch.middlewares.ProxyMiddleware': 843,
    },
    'ITEM_PIPELINES': {
        'CNKIPaSearch.pipelines.SaveHtmlPipeline': 300,
        'CNKIPaSearch.pipelines.FilterPipeline': 301,
        # 'CNKIPaSearch.pipelines.MySQLDetailPipeline': 302,
        # 'CNKIPaSearch.pipelines.SaveJsonPipeline': 302,
    }
}


def start_spider(is_saving_db=False):
    """
    是否存储到数据库
    :param is_saving_db: 默认为False
    :return:
    """
    project_settings = get_project_settings()
    settings = dict(project_settings.copy())
    settings.update(custom_settings)
    # 保存到数据库
    if is_saving_db:
        settings['ITEM_PIPELINES']['CNKIPaSearch.pipelines.MySQLDetailPipeline'] = 302
    else:
        settings['ITEM_PIPELINES']['CNKIPaSearch.pipelines.SaveJsonPipeline'] = 302
    # 合并配置
    process = CrawlerProcess(settings)
    # 启动爬虫
    process.crawl(crawler_or_spidercls='detail')
    process.start()


if __name__ == '__main__':
    start_spider(is_saving_db=True)
