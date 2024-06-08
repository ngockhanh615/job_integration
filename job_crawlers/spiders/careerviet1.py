import scrapy
from datetime import datetime
import re

class CareerVietSpider(scrapy.Spider):
    name = 'careerviet1'
    allowed_domains = ['careerviet.vn']
    start_urls = [f'https://careerviet.vn/viec-lam/cntt-phan-cung-mang-cntt-phan-mem-c63,1-trang-{i}-vi.html' for i in range(1, 50)]  # Adjust the range as needed

    def parse(self, response):
        job_items = response.css('div.job-item')
        for job in job_items:
            title = job.css('div.figcaption > div.title > h2 > a::text').get()
            company_name = job.css('div.figcaption > div.caption > a.company-name::text').get()
            date_posted_raw = job.css('div.figcaption > div.bottom-right-icon > div > time::text').get()
            date_posted = datetime.strptime(date_posted_raw, '%d-%m-%Y').strftime('%H:%M:%S %d-%m-%Y') if date_posted_raw else None
            url = job.css('div.figcaption > div.title.is-red > h2 > a::attr(href)').get()
            salary = job.css('div.figcaption > div.caption > a >div.salary > p::text').get()

            job_url = response.urljoin(url)
            request = scrapy.Request(job_url, callback=self.parse_job_details)
            request.meta['title'] = title.strip() if title else None
            request.meta['company_name'] = company_name
            request.meta['date_posted'] = date_posted
            request.meta['source'] = 'careerviet.vn'
            request.meta['url'] = job_url
            request.meta['salary'] = salary
            yield request

    def parse_job_details(self, response):
        title = response.meta['title']
        company_name = response.meta['company_name']
        date_posted = response.meta['date_posted']
        source = response.meta['source']
        url = response.meta['url']
        salary = response.meta['salary']

        location = response.css('#tab-1 > section > div.bg-blue > div > div:nth-child(1) > div > div > p > a::text').get()

        content = [x.strip() for x in response.css('#tab-1 > section > div.detail-row.reset-bullet > ul > li::text').getall() if x.strip() and re.search(r'\w', x)]
        if not content:
            content = [x.strip() for x in response.xpath('//*[@id="tab-1"]/section/div[3]/p//text()').extract() if x.strip() and re.search(r'\w', x)]
        if not content:
            content = [x.strip() for x in response.css('#tab-1 > section > div.detail-row > p::text').getall() if x.strip() and re.search(r'\w', x)]
        if not content:
            content = [x.strip() for x in response.css('body > main > section.template.template04 > div.bottom-template > div > div > div.col-lg-9-custom  > div.full-content > div:nth-child(2) > div > ul > li::text').getall() if x.strip() and re.search(r'\w', x)]
        if not content:
            content = [x.strip() for x in response.css('#tab-1 > section > div.detail-row.reset-bullet > ul > li > p::text').getall() if x.strip() and re.search(r'\w', x)]
        if not content:
            content = [x.strip() for x in response.css('#tab-1 > section > div.detail-row.reset-bullet > ol:nth-child(3) > li::text').getall() if x.strip() and re.search(r'\w', x)]
        if not content:
            return

        skills = [x.strip() for x in response.css('#tab-1 > section > div.job-tags > ul > li > a::text').getall() if x.strip() and re.search(r'\w', x)]
        if not skills:
            skills = [x.strip() for x in response.css('body > main > section.template.template04 > div.bottom-template > div > div > div.col-lg-9-custom > div.full-content > div.job-tags.detail-row > ul > li > a::text').getall() if x.strip() and re.search(r'\w', x)]
        
        requirement = [x.strip() for x in response.css('#tab-1 > section > div:nth-child(4) > ul:nth-child(2) > li::text').getall() if x.strip() and re.search(r'\w', x)]
        if not requirement:
            requirement = [x.strip() for x in response.css('body > main > section.template.template04 > div.bottom-template > div > div > div.col-lg-9-custom > div.full-content > div:nth-child(3) > div > ul:nth-child(1) > li::text').getall() if x.strip() and re.search(r'\w', x)]
        if not requirement:
            requirement = [x.strip() for x in response.xpath('//*[@id="tab-1"]/section/div[4]/ul[1]/li//text()').extract() if x.strip() and re.search(r'\w', x)]
        if not requirement:
            requirement = [x.strip() for x in response.css('#tab-1 > section > div:nth-child(4) > ul:nth-child(3) > li::text').getall() if x.strip() and re.search(r'\w', x)]
            benefit = [x.strip() for x in response.css('#tab-1 > section > div:nth-child(4) > ul:nth-child(7) > li::text').getall() if x.strip() and re.search(r'\w', x)]
            if not benefit:
                benefit = [x.strip() for x in response.css('#tab-1 > section > div:nth-child(4) > ul:nth-child(6) > li::text').getall() if x.strip() and re.search(r'\w', x)]
            if not benefit:
                benefit = [x.strip() for x in response.css('#tab-1 > section > div:nth-child(4) > ul:nth-child(5) > li::text').getall() if x.strip() and re.search(r'\w', x)]
            if not benefit:
                benefit = [x.strip() for x in response.css('#tab-1 > section > div:nth-child(4) > ul:nth-child(4) > li::text').getall() if x.strip() and re.search(r'\w', x)]
        if not requirement:
            requirement = [x.strip() for x in response.css('#tab-1 > section > div:nth-child(4) > p::text').getall() if x.strip() and re.search(r'\w', x)]
        if not requirement:
            requirement = [x.strip() for x in response.css('#tab-1 > section > div:nth-child(4) > ul:nth-child(3) > li::text').getall() if x.strip() and re.search(r'\w', x)]
            benefit = [x.strip() for x in response.css('#tab-1 > section > div:nth-child(4) > ul:nth-child(5) > li::text').getall() if x.strip() and re.search(r'\w', x)]
        if not requirement:
            requirement = [x.strip() for x in response.css('#tab-1 > section > div:nth-child(4) > ul:nth-child(2) > li > p::text').getall() if x.strip() and re.search(r'\w', x)]
        if not requirement:
            requirement = [x.strip() for x in response.css('#tab-1 > section > div:nth-child(4) > p > strong::text').getall() if x.strip() and re.search(r'\w', x)]
            requirement.extend([x.strip() for x in response.css('#tab-1 > section > div:nth-child(4) > p::text').getall() if x.strip() and re.search(r'\w', x)])
        if not requirement:
            requirement = [x.strip() for x in response.css('#tab-1 > section > div:nth-child(4) > ol > li::text').getall() if x.strip() and re.search(r'\w', x)]
        if not requirement:
            requirement = [x.strip() for x in response.xpath('/html/body/main/section[3]/div[2]/div/div/div[1]/div[3]/div[3]/div//text()').extract() if x.strip() and re.search(r'\w', x)]
        if not requirement:
            requirement = [x.strip() for x in response.xpath('/html/body/main/section[3]/div[2]/div/div/div[1]/div[3]/div[3]/div/ul/li//text()').extract() if x.strip() and re.search(r'\w', x)]

        experience = response.css('#tab-1 > section > div.bg-blue > div > div:nth-child(3) > div > ul > li:nth-child(2) > p::text').get().strip() if response.css('#tab-1 > section > div.bg-blue > div > div:nth-child(3) > div > ul > li:nth-child(2) > p::text').get() else None

        benefit = [x.strip() for x in response.css('#tab-1 > section > div:nth-child(4) > ul:nth-child(4) > li::text').getall() if x.strip() and re.search(r'\w', x)]
        if not benefit:
            benefit = [x.strip() for x in response.css('body > main > section.template.template04 > div.bottom-template > div > div > div.col-lg-9-custom > div.full-content > div:nth-child(3) > div > ul:nth-child(3) > li::text').getall() if x.strip() and re.search(r'\w', x)]
        if not benefit:
            benefit = [x.strip() for x in response.css('#tab-1 > section > div:nth-child(4) > ul:nth-child(10) > li::text').getall() if x.strip() and re.search(r'\w', x)]
        if not benefit:
            benefit = [x.strip() for x in response.css('#tab-1 > section > div:nth-child(4) > ul:nth-child(7) > li > strong::text').getall() if x.strip() and re.search(r'\w', x)]
        if not benefit:
            benefit = [x.strip() for x in response.css('#tab-1 > section > div:nth-child(4) > ul:nth-child(5) > li::text').getall() if x.strip() and re.search(r'\w', x)]
        if not benefit:
            benefit = [x.strip() for x in response.xpath('//*[@id="tab-1"]/section/div[4]/ul[3]/li//text()').extract() if x.strip() and re.search(r'\w', x)]

        if not title:
            # append to log file
            with open('/khanh/airflow/job_crawlers/log/error.log', 'a') as f:
                f.write(f'missing title      : {response.url}\n')
            return
        if not content:
            # append to log file
            with open('/khanh/airflow/job_crawlers/log/error.log', 'a') as f:
                f.write(f'missing content    : {response.url}\n')
            return
        if not requirement:
            # append to log file
            with open('/khanh/airflow/job_crawlers/log/error.log', 'a') as f:
                f.write(f'missing requirement: {response.url}\n')
            return        
        
        yield {
            'title': title,
            'company_name': company_name,
            'date_posted': date_posted,
            'source': source,
            'url': url,
            'salary': salary,
            'location': location,
            'content': content,
            'skills': skills,
            'requirement': requirement,
            'experience': experience,
            'benefit': benefit,
        }
