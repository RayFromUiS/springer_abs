# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class AbsScraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    discipline = scrapy.Field()
    content_type = scrapy.Field()
    article_link = scrapy.Field()
    authors = scrapy.Field()
    pub_time = scrapy.Field()
    source = scrapy.Field()
    journal = scrapy.Field()
    volume = scrapy.Field()
    # page_start = scrapy.Field()
    # page_end = scrapy.Field()
    issue_year = scrapy.Field()
    abstract = scrapy.Field()
    author_aff_address = scrapy.Field()
    citation = scrapy.Field()
    doi = scrapy.Field()
    keywords = scrapy.Field()
    pdf_links = scrapy.Field()
    journal_concat = scrapy.Field()
    backup = scrapy.Field()
    page_number = scrapy.Field()


class OnePetroItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    # discipline = scrapy.Field()
    # content_type = scrapy.Field()
    article_link = scrapy.Field()
    authors = scrapy.Field()
    pub_time = scrapy.Field()
    source = scrapy.Field()
    journal = scrapy.Field()
    # jounral_concat = scrapy.Field()
    volume = scrapy.Field()
    # page_start = scrapy.Field()
    # page_end = scrapy.Field()
    # issue_year = scrapy.Field()
    isbn = scrapy.Field()
    abstract = scrapy.Field()
    author_aff_address = scrapy.Field()
    issue = scrapy.Field()
    # citation = scrapy.Field()
    doi = scrapy.Field()
    keywords = scrapy.Field()
    paper_serial_number = scrapy.Field()
    pdf_links = scrapy.Field()
    journal_concat = scrapy.Field()
    backup = scrapy.Field()
    subjects = scrapy.Field()
    format_con = scrapy.Field()
    publisher= scrapy.Field()
    conference_ser = scrapy.Field()
    page_number = scrapy.Field()

