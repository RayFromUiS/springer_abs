import scrapy
import time
from abs_scraper.items import  AbsScraperItem
from scrapy_redis.spiders import RedisSpider

class SpringerSpider(RedisSpider):
    name = 'springer'
    allowed_domains = ['springer.com']
    start_urls = ['https://link.springer.com/search?facet-content-type=%22Article%22&query=']
    disciplines = ['Chemistry','Physics','Engineering','Materials Science',
                   'Mathematics','Earth Sciences','Environment','Social Sciences',
                   'Economics','Business and Management','Science, Humanities and Social Sciences, multidisciplinary',
                   'Linguistics','Energy','Political Science and International Relations',
                   'Geography','Finance','Materials','Earth Sciences & Geography','Environmental Sciences']

    def start_requests(self):
        for discipline in self.disciplines:
            for url in self.start_urls:
                yield scrapy.Request(url=url+discipline,callback=self.parse_pages,
                                     cb_kwargs={'discipline':discipline})

    def parse_pages(self, response,discipline):
        # print(response.css('title::text').get())
        # print(response.url,response.status_code)
        # from scrapy.shell import inspect_response
        # inspect_response(response,self)

        articles = response.css('ol#results-list li')
        for article in articles:
            article_link = article.css('a').attrib.get('href')
            title = article.css('a::text').get()
            article_type = article.css('p.content-type::text').get().strip()

            yield response.follow(url=article_link,
                                  callback=self.parse,
                                  cb_kwargs={'title':title,
                                             'discipline':discipline,
                                             'article_type':article_type})

        # time.sleep(30)
        next_page = response.css('a.next').attrib.get('href')
        # i = 0
        # while i<3:
        if next_page:
            yield response.follow(url=next_page,callback=self.parse_pages,cb_kwargs={'discipline':discipline})
                # i =i+1
            # from scrapy.shell import inspect_response
            # inspect_response(response,self)
    def parse(self,response,title,discipline,article_type):
        # from scrapy.shell import inspect_response
        # inspect_response(response,self)

        item = AbsScraperItem()
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
                        if response.xpath("//span[@itemprop='name']")  \
                        else response.xpath("//li[@class='c-author-list__item']").css('a::text').getall()
        # item['']
        item['journal'] = response.xpath("//i[@data-test='journal-title']/text()").get()
        item['volume'] = response.xpath("//b[@data-test='journal-volume']/text()").get().strip()
        # item['page_start'] = response.xpath("//span[@itemprop='pageStart']/text()").get()
        # item['page_end'] = response.xpath("//span[@itemprop='pageEnd']/text()").get()
        item['issue_year'] = response.xpath("//span[@data-test='article-publication-year']/text()").get().strip()
        item['abstract'] =  response.css('div#Abs1-content p::text').get()
        item['author_aff_address'] = response.css('p.c-article-author-affiliation__address::text').get()
        item['doi'] = response.xpath("//a[@itemprop='sameAs']").attrib.get('href')
        item['keywords']= response.xpath("//span[@itemprop='about']/text()").getall()
        item['pdf_links'] = response.xpath("//a[@data-track-action='download pdf']").attrib.get('href')
        cites = response.css('p.c-bibliographic-information__citation *::text').getall()
        cite_pro = []
        for i in range(len(cites)):
            if i == 0:
                cite_pro.append(cites[i].strip())
                continue
            else:
                cite_pro.append(cites[i])
        item['citation'] =''.join(cite_pro)
        item['journal_concat'] = item['citation'].split('https:')[0].split('.')[-2].strip()


        yield item









