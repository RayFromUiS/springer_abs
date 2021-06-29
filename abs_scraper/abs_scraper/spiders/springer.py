import scrapy
import time
import re
import random
import easyocr
import json
from abs_scraper.items import AbsScraperItem,OnePetroItem
from scrapy.http import HtmlResponse
from scrapy_redis.spiders import RedisSpider
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from abs_scraper.helpers import get_text
from scrapy.utils.project import get_project_settings
from easyocr  import Reader
import pymongo
from scrapy_redis.spiders import  RedisSpider

class SpringerSpider(RedisSpider):
    name = 'springer'
    # allowed_domains = ['springer.com']
    redis_key = "springer:start_urls"
    # disciplines = ['Chemistry', 'Physics', 'Engineering', 'Materials Science',
    #                'Mathematics', 'Earth Sciences', 'Environment', 'Social Sciences',
    #                'Economics', 'Business and Management', 'Science, Humanities and Social Sciences, multidisciplinary',
    #                'Linguistics', 'Energy', 'Political Science and International Relations',
    #                'Geography', 'Finance', 'Materials', 'Earth Sciences & Geography', 'Environmental Sciences']

    def __init__(self):
        self.mongo_uri = get_project_settings().get('MONGO_URI')
        self.mongo_db = get_project_settings().get('MONGO_DATABASE')
        # self.collection
        # self.discipline = random.choice(self.disciplines)
        # self.collection = 'spr_abs_'+ str(self.discipline)\
        self.collection = 'Chemistry'
        # self.discipline = 'Earth Sciences'
        # self.collection = 'spr_abs_' + self.discipline
        # self.discipline = s
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]


    def make_requests_from_url(self, url):
        page = url.split('/page/')[-1].split('?')[0]
        # self.collection = url.split('==')[-1]
        return SeleniumRequest(url=url ,
                                      # callback=self.parse_pages,
                                      wait_time=30,
                                      # wait_until=EC.presence_of_element_located((By.XPATH, '//a[@class="next"]')),
                                      # wait_until=EC.new_window_is_opened,
                                      cb_kwargs={'discipline': self.collection
                                          , 'page_number': page
                                                 }
                                      )


    def parse(self, response, discipline, page_number):

        results = []
        title_page = response.css('title::text').get()
        if not re.search('Error', title_page):  # no error page is shown
            articles = response.css('ol#results-list li')
            for article in articles:
                article_link = article.css('a').attrib.get('href')
                title = article.css('a::text').get()
                article_type = article.css('p.content-type::text').get().strip()
                # if the article is not scraped
                if not self.db[self.collection].find_one({'article_link': article_link}):

                    yield response.follow(url=article_link,
                                          callback=self.parse_item,
                                          cb_kwargs={'title': title,
                                                     'discipline': discipline,
                                                     'article_type': article_type,
                                                     'page_number': page_number})
                results.append(article_link)
                if len([result for result in results if result is not None]) == len(results):
                    break

        elif re.search('Error', title_page):  ## error page is shown
            time.sleep(3)
            url = response.url
            yield SeleniumRequest(url=url,
                                  callback=self.parse,
                                  wait_time=60,
                                  # wait_until=EC.presence_of_element_located((By.XPATH, '//a[@class=""]')),
                                  cb_kwargs={'discipline': discipline,
                                             'page_number': page_number
                                             }
                                  )


    def parse_item(self, response, title, discipline, article_type, page_number):
        # from scrapy.shell import inspect_response
        # inspect_response(response,self)

        item = AbsScraperItem()
        item['page_number'] = page_number
        item['discipline'] = discipline
        item['content_type'] = article_type
        item['title'] = title
        item['article_link'] = response.url
        item['pub_time'] = response.xpath("//time[@itemprop='datePublished']").attrib.get('datetime')
        # num_authors =len(response.xpath("//span[@itemprop='name']"))
        # for author in response.xpath("//span[@itemprop='name']"):
        #     item['first_author'] = response.xpath("//span[@itemprop='name']")[0].css('a::text').get()
        #     item['second_author'] = response.xpath("//span[@itemprop='name']")[1].css('a::text').get()
        item['authors'] = response.xpath("//span[@itemprop='name']").css('a::text').getall() \
            if response.xpath("//span[@itemprop='name']") \
            else response.xpath("//li[@class='c-author-list__item']").css('a::text').getall()
        item['journal'] = response.xpath("//i[@data-test='journal-title']/text()").get()
        item['volume'] = response.xpath("//b[@data-test='journal-volume']/text()").get().strip()
        # item['page_start'] = response.xpath("//span[@itemprop='pageStart']/text()").get()
        # item['page_end'] = response.xpath("//span[@itemprop='pageEnd']/text()").get()
        item['issue_year'] = response.xpath("//span[@data-test='article-publication-year']/text()").get().strip()
        item['abstract'] = response.xpath('//div[@id="Abs1-content"]/p//text()').getall()
        item['author_aff_address'] = response.css('p.c-article-author-affiliation__address::text').get()
        item['doi'] = response.xpath("//a[@itemprop='sameAs']").attrib.get('href')
        item['keywords'] = response.xpath("//span[@itemprop='about']/text()").getall()
        item['pdf_links'] = response.xpath("//a[@data-track-action='download pdf']").attrib.get('href')
        cites = response.css('p.c-bibliographic-information__citation *::text').getall()
        cite_pro = []
        for i in range(len(cites)):
            if i == 0:
                cite_pro.append(cites[i].strip())
                continue
            else:
                cite_pro.append(cites[i])
        item['citation'] = ''.join(cite_pro)
        item['journal_concat'] = item['citation'].split('https:')[0].split('.')[-2].strip()
        yield item

# class OnePetroSpider(RedisSpider):
#     name = 'one_petro'
#     redis_key = "one_petro:start_urls"
#
#     custom_settings = {
#         'ITEM_PIPELINES': {'abs_scraper.pipelines.OnePetroPipeline': 301},
#     }
#     def __init__(self):
#         self.mongo_uri = get_project_settings().get('MONGO_URI')
#         self.mongo_db = get_project_settings().get('MONGO_DATABASE')
#         self.collection = 'one_petro'
#         self.client = pymongo.MongoClient(self.mongo_uri)
#         self.db = self.client[self.mongo_db]
#
#
#     def make_requests_from_url(self, url):
#         return SeleniumRequest(url=url ,
#                                       # callback=self.parse_pages,
#                                       wait_time=10,
#
#                                       )
#
#     def parse_crawl(self, response):
#         '''
#         parse data
#         '''
#         # from scrapy.shell import  inspect_response
#         # inspect_response(response.self)
#         driver = response.meta.get('driver')
#         if re.search('crawlpre',response.url):
#             #get image
#             text = get_text(response.url)
#             driver.find_element_by_tag_name('input').send_keys(str(text))
#             driver.find_element_by_tag_name('button').click()
#             url = driver.current_url
#             res = HtmlResponse(boby=driver.page_source,url=url)
#             # self.make_requests_from_url(url)
#         return res
#
#     def parse(self,response):
#         if re.search('crawlpre', response.url):
#             res = self.parse_crawl(response)
#             return self.parse_item(res)
#         else:
#             return self.parse_item(response)
#
#     def parse_item_dict_before(self, response,pdf_downloading_link,article_title,volume,issue):
#         #
#         if re.search('crawlpre', response.url):
#             res = self.parse_crawl(response)
#             return self.parse_item_dict(res,pdf_downloading_link,article_title,volume,issue)
#         else:
#             return self.parse_item_dict(response,pdf_downloading_link,article_title,volume,issue)
#
#     def parse_item(self,response):
#         volume = response.url.split('/')[-2]
#         issue = response.url.split('/')[-1]
#         articles = response.css('div.content.al-article-list-group').css('div.al-article-items')
#         for article in articles:
#             article_link = article.css('div.al-article-items').css('h5 a').attrib.get('href')
#             article_link = response.urljoin(article_link)
#             article_title = article.css('div.al-article-items').css('h5 a::text ').get()
#             pdf_downloading_link =  article.css('a.article-pdfLink').attrib.get('href') if \
#                 article.css('a.article-pdfLink') else None
#             pdf_downloading_link = response.urljoin(pdf_downloading_link)
#
#             if not self.db[self.collection].find_one({'article_link': article_link}):
#                 # yield SeleniumRequest(
#                 yield scrapy.Request(
#                     url=article_link,
#                     callback=self.parse_item_dict_before,
#                     cb_kwargs={
#                         'article_title': article_title,
#                         'pdf_downloading_link': pdf_downloading_link,
#                         'volume':volume,
#                         'issue':issue
#                     },
#
#                 )
#
#
#
#     def parse_item_dict(self, response, pdf_downloading_link,article_title,volume,issue):
#         '''
#         parse html and store inside item accordingly
#         '''
#
#         # from scrapy.shell import inspect_response
#         # inspect_response(response, self)
#         item = OnePetroItem()
#         item['title'] = article_title
#         # item['author_aff_address'] = None
#         item['pub_time'] = response.css('span.article-date::text').get()
#         article_authors = response.css('div#authorInfo_ArticleTopInfo_Abstract div.info-card-name::text').getall()
#         item['authors']= [author.strip() for author in article_authors if author]
#         item['author_aff_address'] = response.css('div#authorInfo_ArticleTopInfo_Abstract div.aff::text').get()
#         item['volume'] = volume
#         item['issue'] = issue
#         item['article_link'] = response.url
#         jounal = response.css('div.ww-citation-primary em::text').get()
#         volume_issue = response.css('div.ww-citation-primary::text').get()
#         if jounal and volume_issue:
#             item['journal_concat'] = jounal+volume_issue
#         else:
#             item['journal_concat'] = None
#
#         if volume_issue:
#             item['page_number'] = volume_issue.split(':')[-1].strip().replace('.','')
#         else:
#             item['page_number'] = None
#
#
#         # item['article_title'] = response.xpath('//*[@id="screen-reader-main-title"]/span//text()').getall()
#         # item['article_title'] = article_title
#         item['doi'] = response.css('div.citation-doi a').attrib.get('href')
#         paper_serial_number = item['doi'].split('/')[-1] if item['doi'] else None
#         # item['page_number'] = paper_number
#
#         item['paper_serial_number'] = 'SPE'+'-'+ paper_serial_number  if paper_serial_number  else None
#
#         item['abstract'] = response.css('section.abstract p::text').get()
#         item['keywords'] =  response.css('div.content-metadata-keywords a::text').getall()
#         item['pdf_links'] = pdf_downloading_link
#         item['subjects'] = response.css('div.content-metadata-facetcategoryids a::text').getall()
#         item['source'] = 'https://onepetro.org'
#         yield item




class OnePetroUpdatedSpider(scrapy.Spider):
    name = 'one_petro'
    # redis_key = "one_petro:start_urls"

    # start_urls = ['https://onepetro.org/search-results?sort=Date'
    #               '+-+Newest+First&fl_SiteID=1&rg_PublicationDate='
    #               '01%2f01%2f2020+TO+05%2f31%2f2021&page=3&f_ContentType=Proceedings+Papers']
    start_urls = ['https://onepetro.org/search-results?sort=Date'
                  '+-+Newest+First&fl_SiteID=1&rg_PublicationDate='
                  '01%2f01%2f2020+TO+05%2f31%2f2021&page=1&f_ContentType=Journal+Articles']
    custom_settings = {
        'ITEM_PIPELINES': {'abs_scraper.pipelines.OnePetroPipeline': 301},
    }
    def __init__(self):
        self.mongo_uri = get_project_settings().get('MONGO_URI')
        self.mongo_db = get_project_settings().get('MONGO_DATABASE')
        self.collection = 'one_petro'
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.reader = easyocr.Reader(['en'], gpu=False)

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(url=url ,
                                      callback=self.parse_pages,
                                      wait_time=60,
                                      # wait_until=EC.presence_of_element_located((By.ID, 'ContentColumn'))
                                      #
                                      )

    # def parse_crawl(self, response):
    #     '''
    #     parse data
    #     '''
    #     # from scrapy.shell import  inspect_response
    #     # inspect_response(response.self)
    #     driver = response.meta.get('driver')
    #     reader = easyocr.Reader(['en'], gpu=False)
    #     # print('the respponse url is ',response.url)
    #     print('the current url of driver is ',driver.current_url)
    #     driver.save_screenshot('window.png')
    #     if re.search('crawlpre',response.url):
    #         driver.maximize_window()
    #         img_tag= driver.find_element_by_xpath('//div[@class="container"]/div/img')
    #         # print(len(img_eles))
    #         # img_eles.save_screenshot('img.png')
    #         # for ele in img_eles:
    #         #     ele.screenshot('img.png')
    #
    #         # img_tag = img_eles[-1]
    #         # img_name = random.randint()
    #         img_tag.screenshot('test.png')
    #         text = reader.readtext('test.png', detail=0)
    #         text = ''.join(text)
    #         time.sleep(5)
    #         # driver.find_element_by_tag_name('input').click()
    #         driver.find_element_by_tag_name('input').send_keys(str(text))
    #         time.sleep(4)
    #         driver.find_element_by_tag_name('button').screenshot('button.png')
    #         driver.find_element_by_tag_name('button').click()
    #         el = WebDriverWait(driver,180).until(lambda d: d.find_element_by_id("ContentColumn"))
    #         time.sleep(20)
    #         print(driver.current_url)
    #         url = driver.current_url
    #         res = HtmlResponse(body=driver.page_source,url=url,encoding='utf8')
    #         # self.make_requests_from_url(url)
    #     return res

    # def parse(self,response):
    # #
    #     # try_times = 0
    #     # while try_times<3 and \
    #     if re.search('crawlpre', response.url):
    #         res = self.parse_crawl(response)
    #         if not re.search('crawlpre', res.url):
    #             return self.parse_items_per_page(res)
    #         else:
    #             print(res.css('title'),res.url,'there is another crawl prevention')
    #
    #         # else:
    #         #     try_times += 1
    #     if not re.search('crawlpre', response.url) and not re.search('Not',response.css('title::text').get()):
    #         return self.parse_items_per_page(response)
    #
    #     if  re.search('Not',response.css('title::text').get()):
    #         return SeleniumRequest(url=response.url,
    #                                callback=self.parse_item,
    #                                wait_time=20,
    #                                wait_until=EC.presence_of_element_located((By.XPATH, '//div[@class="pagination-bottom-outer-wrap"]')))
    #
    #     # if re.search('Not',response.css('title::text').get()):
    #     #     try:
        #         driver = response.meta.get('driver')
        #         driver.find_element_by_xpath('//div[@class="gdpr-cookie-links_wrap"]').click()
        #
        #     except:


    # def parse_next_page(self,response):
    #     # from scrapy.shell import inspect_response
    #     # inspect_response(response,self)
    #     print('the response url is ',response.url)
    #     driver = response.meta.get('driver')
    #     print('the driver current ulr is ',driver.current_url)
    #     driver.get(response.url)
    #     print('the driver current ulr is ',driver.current_url)
    #     el = WebDriverWait(driver,60).until(lambda d: d.find_element_by_id("ContentColumn"))
    #     driver.find_element_by_xpath('//a[contains(@class,"js-gdpr-cookie-acceptLink")]').screenshot('cookie.png')
    #     driver.find_element_by_xpath('//a[contains(@class,"js-gdpr-cookie-acceptLink")]').click()
    #     driver.save_screenshot('next_page.png')
    #     # print(driver.current_url)
    #     next_page = driver.find_element_by_xpath('//div[@class="pagination-bottom-outer-wrap"]').find_elements_by_tag_name('a')[-1]
    #     #find next page
    #     # next_page =driver.find_element_by_xpath('//a[contains(@class,"al-nav-next")]')
    #     if next_page:
    #         next_page.click()
    #         el = WebDriverWait(driver,150).until(lambda d: d.find_element_by_id("ContentColumn"))
    #         body = driver.page_source
    #         url = driver.current_url
    #         print('the new url is',url)
    #         res = HtmlResponse(body=body,
    #                            url=url,
    #                            encoding='utf8')
    #         return res


            # yield SeleniumRequest(url=url,
            #                       callback=self.parse,
            #                       wait_time=20,
            #                       # wait_until=EC.presence_of_element_located((By.XPATH, '//div[@class="pagination-bottom-outer-wrap"]'))
            #                       )

    # def parse_item_dict_before(self, response, pdf_downloading_link,article_title,\
    #                     doi,paper_serial_number,format_con,publisher,conference_ser):
    #     #
    #     # try_times = 0
    #     if re.search('crawlpre', response.url):
    #         res = self.parse_crawl(response)
    #         if not re.search('crawlpre', res.url):
    #             return self.parse_item_dict(res, pdf_downloading_link,article_title,\
    #                     doi,paper_serial_number,format_con,publisher,conference_ser)
    #         # else:
    #         #     try_times += 1
    #     if not re.search('crawlpre', response.url) and not re.search('Not',response.css('title::text').get()):
    #         return self.parse_item_dict( response, pdf_downloading_link,article_title,\
    #                     doi,paper_serial_number,format_con,publisher,conference_ser)



    # def parse_next_page(self,next_page):


    def parse_item(self,response):
        # from scrapy.shell import  inspect_response
        # inspect_response(response,self)
        # spider_cb_kwargs = {}
        # driver = response.meta.get('driver')
        articles = response.css('div.sr-list_wrap').css('div.item-container')
        spider_cb_kwargs = []
        for i in range(len(articles)):
            spider_cb_kwarg = {}
            # format_con = articles[i].css('span.sri-type::text').get()
            format_con='jounral article'
            jounral = ''
            # publisher = articles[i].xpath("//span[@class='sri-label']//following-sibling::a/text()")[i].get()
            jounral = articles[i].xpath("//span[@class='sri-label']//following-sibling::a/text()").get().strip()
            publisher = articles[i].xpath("//div[@class='sri-publisher-name']/a/text()").get()
            article_title = articles[i].css('h4 a::text').get()
            article_link = articles[i].css('h4 a').attrib.get('href')
            article_link = response.urljoin(article_link)
            con_ser_pre = response.css('div.al-citation-list em::text').get()
            con_ser_suf = response.css('div.al-citation-list span::text').get()
            conference_ser = con_ser_pre+con_ser_suf if (con_ser_pre and con_ser_suf) else None
            # conference_ser = articles[i].css('div.al-citation-list span//text').get()
            pdf_downloading_link = articles[i].css('div.resource-links-info').css('a.pdf').attrib.get('href') \
                    if articles[i].css('div.resource-links-info').css('a.pdf') else None
            pdf_downloading_link = response.urljoin(pdf_downloading_link)
            doi = articles[i].css('div.citation-label a').attrib.get('href')
            paper_serial_number = articles[i].css('div.citation-label::text').get()
            spider_cb_kwarg['article_link'] = article_link
            spider_cb_kwarg['article_title'] = article_title
            spider_cb_kwarg['jounral'] = jounral
            spider_cb_kwarg['pdf_downloading_link'] = pdf_downloading_link
            spider_cb_kwarg['format_con'] = format_con
            spider_cb_kwarg['doi'] = doi
            spider_cb_kwarg['paper_serial_number'] = paper_serial_number
            spider_cb_kwarg['publisher'] = publisher
            spider_cb_kwarg['conference_ser'] = conference_ser
            spider_cb_kwargs.append(spider_cb_kwarg)

        return spider_cb_kwargs


            # if not self.db[self.collection].find_one({'article_link': article_link}):
            #         # yield (
            #     yield SeleniumRequest(
            #             url=article_link,
            #             callback=self.parse_item_dict_before,
            #             cb_kwargs={
            #                 'article_link':article_link,
            #                 'article_title': article_title,
            #                 'pdf_downloading_link': pdf_downloading_link,
            #                 'format_con':format_con,
            #                 'doi':doi,
            #                 'paper_serial_number':paper_serial_number,
            #                 'publisher':publisher,
            #                 'conference_ser':conference_ser})

            # next_page = response.css('div.pagination-bottom-outer-wrap a')[-1].attrib.get('data-url')
            #click cookie acceptance
    def parse_pages(self,response):
        page_num = 1
        while page_num<1000:
            next_url=f"""https://onepetro.org/search-results?sort=Date+-+Newest+First&fl_SiteID=1&rg_" \
                     "PublicationDate=01%2f01%2f2020+TO+05%2f31%2f2021&page={page_num}&f_ContentType=Journal+Articles"""
            page_num += 1
            yield SeleniumRequest(url=next_url,
                              callback=self.parse_items_per_page,
                              wait_time=30,
                              # wait_until=EC.presence_of_element_located((By.ID, 'ContentColumn'))
                                  )

            # time.sleep(10)

    def parse_items_per_page(self,response):
        # from scrapy.shell import inspect_response
        # inspect_response(response,self)
        spider_cb_kwargs = self.parse_item(response)
        for spider_cb_kwarg in spider_cb_kwargs:
            if not self.db[self.collection].find_one({'article_link':spider_cb_kwarg.get('article_link')}):
                yield SeleniumRequest(
                    url=spider_cb_kwarg.get('article_link'),
                    callback=self.parse_item_dict,
                    cb_kwargs={
                        'article_title': spider_cb_kwarg.get('article_title'),
                        'journal': spider_cb_kwarg.get('journal'),
                        'pdf_downloading_link':spider_cb_kwarg.get('pdf_downloading_link'),
                        'format_con':spider_cb_kwarg.get('format_con'),
                        'doi':spider_cb_kwarg.get('doi'),
                        'paper_serial_number':spider_cb_kwarg.get('paper_serial_number'),
                        'publisher':spider_cb_kwarg.get('publisher'),
                        'conference_ser':spider_cb_kwarg.get('conference_ser')
                    }
                        )

        # time.sleep(20)
        # res = self.parse_next_page(response)


    # def parse_item_dict(self, response, journal,pdf_downloading_link,article_title,\
    #                     doi,paper_serial_number,format_con,publisher,conference_ser):
    #     '''
    #     parse html and store inside item accordingly
    #     '''
    #     # from scrapy.shell import inspect_response
    #     # inspect_response(response,self)
    #     # from scrapy.shell import inspect_response
    #     # inspect_response(response, self)
    #     item = OnePetroItem()
    #     item['title'] = article_title
    #     item['format_con'] = format_con
    #     item['publisher'] = publisher
    #     item['conference_ser'] = conference_ser
    #     isbns = response.css('div.conference-volume-isbn_wrap div::text').getall()
    #     new_isbns = [i.strip() for i in isbns]
    #     item['isbn'] = ''.join(new_isbns) if new_isbns else None
    #     item['pub_time'] = response.css('span.paper-date::text').get()
    #     item['doi'] = doi
    #     item['paper_serial_number'] = paper_serial_number
    #     article_authors = response.css('div.al-author-info-wrap div.info-card-name::text').getall()
    #     item['authors']= [author.strip() for author in article_authors if author]
    #     aff_addresses = response.css('div.al-author-info-wrap div.info-card-affilitation div.aff::text').getall()
    #     aff_address = aff_addresses[0] if aff_addresses else None
    #     item['author_aff_address'] = aff_address
    #     item['volume'] = None
    #     item['issue'] = None
    #     item['article_link'] = response.url
    #     item['journal_concat'] = journal
    #     item['page_number'] = None
    #     item['abstract'] = response.css('section.abstract p::text').getall()
    #     item['keywords'] =  response.css('div.content-metadata-keywords a::text').getall()
    #     item['pdf_links'] = pdf_downloading_link
    #     item['subjects'] = response.css('div.content-metadata-facetcategoryids a::text').getall()
    #     item['source'] = 'https://onepetro.org'

    def parse_item_dict(self, response, journal,pdf_downloading_link,article_title, \
                            doi,paper_serial_number,format_con,publisher,conference_ser):
        '''
        parse html and store inside item accordingly
        '''
        # from scrapy.shell import inspect_response
        # inspect_response(response,self)
        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
        item = OnePetroItem()
        item['title'] = article_title
        item['format_con'] = format_con
        item['publisher'] = publisher
        item['conference_ser'] = conference_ser
        item['journal'] = journal
        isbns = response.css('div.conference-volume-isbn_wrap div::text').getall()
        new_isbns = [i.strip() for i in isbns]
        item['isbn'] = ''.join(new_isbns) if new_isbns else None
        item['pub_time'] = response.css('span.article-date::text').get()
        item['doi'] = doi
        item['paper_serial_number'] = paper_serial_number
        article_authors = response.css('div.al-author-info-wrap div.info-card-name::text').getall()
        item['authors']= [author.strip() for author in article_authors if author]
        aff_addresses = response.css('div.al-author-info-wrap div.info-card-affilitation div.aff::text').getall()
        aff_address = aff_addresses[0] if aff_addresses else None
        item['author_aff_address'] = aff_address
        item['volume'] = None
        item['issue'] = None
        item['article_link'] = response.url
        jounral_concat_pre = response.css('div.ww-citation-primary em::text').get()
        jounral_concat_suf = response.css('div.ww-citation-primary::text').get()
        item['journal_concat'] = jounral_concat_pre+jounral_concat_suf if (jounral_concat_pre and jounral_concat_suf) else None
        item['page_number'] = None
        item['abstract'] = response.css('section.abstract p::text').getall()
        item['keywords'] =  response.css('div.content-metadata-keywords a::text').getall()
        item['pdf_links'] = pdf_downloading_link
        item['subjects'] = response.css('div.content-metadata-facetcategoryids a::text').getall()
        item['source'] = 'https://onepetro.org'



        yield item

