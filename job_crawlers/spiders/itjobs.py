import scrapy


class ItjobsSpider(scrapy.Spider):
    name = "itjobs"
    allowed_domains = ["itjobs.com.vn"]
    start_urls = ["https://itjobs.com.vn"]

    def parse(self, response):
        pass
