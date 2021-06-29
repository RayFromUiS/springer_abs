# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from __future__ import absolute_import
import os
import os.path
import logging
import pickle
from scrapy import signals
import re
from selenium.webdriver.support.ui import WebDriverWait
from scrapy.http import HtmlResponse

import time
# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter

from scrapy.http.cookies import CookieJar

from scrapy.downloadermiddlewares.cookies import CookiesMiddleware
from abs_scraper import settings


class AbsScraperSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class AbsScraperDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        reader = spider.reader
        driver = response.meta.get('driver')
        # print('the respponse url is ',response.url)
        print('the current url of driver is ',driver.current_url)
        driver.save_screenshot('window.png')
        if re.search('crawlpre',response.url):
            driver.maximize_window()
            img_tag= driver.find_element_by_xpath('//div[@class="container"]/div/img')
            img_tag.screenshot('test.png')
            text = reader.readtext('test.png', detail=0)
            text = ''.join(text)
            time.sleep(4)
            # driver.find_element_by_tag_name('input').click()
            print('the verification code is ',text)
            driver.find_element_by_tag_name('input').send_keys(str(text))
            time.sleep(3)
            driver.find_element_by_tag_name('button').screenshot('button.png')
            driver.find_element_by_tag_name('button').click()
            # el = WebDriverWait(driver,180).until(lambda d: d.find_element_by_id("Sidebar"))
            # time.sleep(20)
            print(driver.current_url)
            url = driver.current_url
            res = HtmlResponse(body=driver.page_source,url=url,encoding='utf8')
            return res
        elif not re.search('crawlpre', response.url) and not re.search('Not',response.css('title::text').get()):
            return response
        else:
            return request


    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)




class PersistentCookiesMiddleware(CookiesMiddleware):
    def __init__(self, debug=False):
        super(PersistentCookiesMiddleware, self).__init__(debug)
        self.load()

    def process_response(self, request, response, spider):
        # TODO: optimize so that we don't do it on every response
        res = super(PersistentCookiesMiddleware, self).process_response(request, response, spider)
        self.save()
        return res

    def getPersistenceFile(self):
        return settings.COOKIES_STORAGE_FILE

    def save(self):
        logging.debug("Saving cookies to disk for reuse")
        with open(self.getPersistenceFile(), "wb") as f:
            pickle.dump(self.jars, f)
            f.flush()

    def load(self):
        filename = self.getPersistenceFile()
        logging.debug("Trying to load cookies from file '{0}'".format(filename))
        if not os.path.exists(filename):
            logging.info("File '{0}' for cookie reload doesn't exist".format(filename))
            return
        if not os.path.isfile(filename):
            raise Exception("File '{0}' pis not a regular file".format(filename))

        with open(filename, "rb") as f:
            self.jars = pickle.load(f)
