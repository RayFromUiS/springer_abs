import scrapy
import time
import re
import random
from abs_scraper.items import AbsScraperItem
from scrapy_redis.spiders import RedisSpider
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from scrapy.utils.project import get_project_settings
import pymongo


class SpringerSpider(scrapy.Spider):
    name = 'springer'
    # allowed_domains = ['springer.com']
    start_urls = ['https://link.springer.com/search?facet-content-type=%22Article%22&query=']
    disciplines = ['Chemistry', 'Physics', 'Engineering', 'Materials Science',
                   'Mathematics', 'Earth Sciences', 'Environment', 'Social Sciences',
                   'Economics', 'Business and Management', 'Science, Humanities and Social Sciences, multidisciplinary',
                   'Linguistics', 'Energy', 'Political Science and International Relations',
                   'Geography', 'Finance', 'Materials', 'Earth Sciences & Geography', 'Environmental Sciences']

    def __init__(self):
        self.mongo_uri = get_project_settings().get('MONGO_URI')
        self.mongo_db = get_project_settings().get('MONGO_DATABASE')
        # self.collection
        # self.discipline = random.choice(self.disciplines)
        # self.collection = 'spr_abs_'+ str(self.discipline)\
        self.collection = None
        # self.discipline = 'Earth Sciences'
        # self.collection = 'spr_abs_' + self.discipline
        # self.discipline = s
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def start_requests(self):

        for url in self.start_urls:
            for discipline in self.disciplines:
                self.collection = 'spr_abs'+str(discipline)
                yield SeleniumRequest(url=url + str(discipline),
                                      callback=self.parse_pages,
                                      wait_time=60,
                                      # wait_until=EC.presence_of_element_located((By.XPATH, '//a[@class="next"]')),
                                      # wait_until=EC.new_window_is_opened,
                                      cb_kwargs={'discipline': discipline
                                                 ,'page_number':1
                                                 }
                                      )

    def parse_pages(self, response, discipline,page_number):
        # from scrapy.shell import inspect_response
        # inspect_response(response,self)
        results = []
        title_page = response.css('title::text').get()
        driver = response.meta.get('driver')
        driver.set_page_load_timeout(180)
        if not re.search('Error', title_page) :  # no error page is shown
            # if page_number == 1:
            try:
                driver.find_element_by_id('onetrust-accept-btn-handler').click()
                ele = WebDriverWait(driver, 30).until(
                            EC.invisibility_of_element((By.ID, "onetrust-policy")))
                driver.find_element_by_link_text('Newest First').click()
                time.sleep(10)
            except:
                pass
            finally:
                # ele = WebDriverWait(driver, 30).until(
                #         EC.((By.XPATH, '//a[@class="next"]')))
                    ## after click or not proceed with following actions
                articles = response.css('ol#results-list li')
                for article in articles:
                    article_link = article.css('a').attrib.get('href')
                    title = article.css('a::text').get()
                    article_type = article.css('p.content-type::text').get().strip()
                    # if the article is not scraped
                    if not self.db[self.collection].find_one({'article_link': article_link}):
                        results.append(article_link)
                        yield response.follow(url=article_link,
                                              callback=self.parse,
                                              cb_kwargs={'title': title,
                                                         'discipline': discipline,
                                                         'article_type': article_type,
                                                         'page_number':page_number})

                    else: ## if the aritcle has been scraped
                        results.append(None)
                if len([result for result in results if result is not None]) == len(results):
                    # time.sleep(3)
                    num_pages = response.xpath('//span[@class="number-of-pages"]/text()').get()
                    if re.search(r',',num_pages):
                        num_pages = int(num_pages.replace(',',''))
                    else:
                        num_pages = int(num_pages)
                    for i in range(2,num_pages+1):
                        page_url =f'https://link.springer.com/search/page/{i}?facet-content-type=%22Article%22&query=Earth+Sciences'
                        yield SeleniumRequest(url=page_url,
                                              callback=self.parse_links,
                                              wait_time=30,
                                              # wait_until=EC.presence_of_element_located(
                                              #     (By.XPATH, '//a[@class="next"]')),
                                              cb_kwargs={'discipline': discipline,
                                                         'page_number':i
                                                         }
                                              )

        elif re.search('Error', title_page):  ## error page is shown
            time.sleep(3)
            url = response.url
            yield SeleniumRequest(url=url,
                                  callback=self.parse_pages,
                                  wait_time=60,
                                  # wait_until=EC.presence_of_element_located((By.XPATH, '//a[@class="next"]')),
                                  cb_kwargs={'discipline': discipline
                                             ,'page_unumber':page_number
                                             }
                                  )

    def parse_links(self,response,discipline,page_number):

        # results = []
        title_page = response.css('title::text').get()
        if not re.search('Error', title_page):  # no error page is shown
            articles = response.css('ol#results-list li')
            for article in articles:
                article_link = article.css('a').attrib.get('href')
                title = article.css('a::text').get()
                article_type = article.css('p.content-type::text').get().strip()
                # if the article is not scraped
                if not self.db[self.collection].find_one({'article_link': article_link}):
                    # results.append(article_link)
                    yield response.follow(url=article_link,
                                          callback=self.parse,
                                          cb_kwargs={'title': title,
                                                     'discipline': discipline,
                                                     'article_type': article_type,
                                                     'page_number': page_number})


        elif re.search('Error', title_page):  ## error page is shown
            time.sleep(3)
            url = response.url
            yield SeleniumRequest(url=url,
                                  callback=self.parse_links,
                                  wait_time=60,
                                  # wait_until=EC.presence_of_element_located((By.XPATH, '//a[@class=""]')),
                                  cb_kwargs={'discipline': discipline,
                                             'page_number': page_number
                                             }
                                  )
        # if len([result for result in results if result is not None]) == len(results):



    def parse(self, response, title, discipline, article_type,page_number):
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
