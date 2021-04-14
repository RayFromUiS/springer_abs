
from scrapy.crawler import CrawlerRunner,CrawlerProcess
from scrapy.utils.log import configure_logging

from abs_scraper.spiders.news_oe_offshore import  SpringerSpider
from scrapy.settings import Settings
from abs_scraper import settings


def run_scraper():
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)
    configure_logging()
    # runner = CrawlerRunner(settings=crawler_settings)
    # task = LoopingCall(lambda: runner.crawl(NewsOeOffshoreSpider))
    # task.start(6000 * 100)
    # reactor.run()
    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(SpringerSpider)
    process.start()


if __name__ == "__main__":
    run_scraper()