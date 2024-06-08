import scrapy


class ItviecSpider(scrapy.Spider):
    name = "itviec"
    allowed_domains = ["itviec.com"]
    start_urls = ["https://itviec.com"]

    def parse(self, response):
        pass
