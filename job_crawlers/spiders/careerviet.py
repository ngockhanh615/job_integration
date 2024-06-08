import scrapy
from parsel import Selector
from datetime import datetime
import re

class CareervietSpider(scrapy.Spider):
    name = "careerviet"
    allowed_domains = ["careerviet.vn"]
    start_urls = ["https://careerviet.vn/viec-lam/cntt-phan-cung-mang-cntt-phan-mem-c63,1-trang-1-vi.html"]

    def parse(self, response):
        # Get all job URLs and date posted on the current page
        job_items = response.css('[id^=job-item]')
        for job_item in job_items:
            detail_url = job_item.css('div.figcaption > div.title.is-red > h2 > a::attr(href)').get()
            date_posted = job_item.css('div.figcaption > div.bottom-right-icon > div > time::text').get()
            if detail_url:
                yield response.follow(detail_url, self.parse_job_details, meta={'date_posted': date_posted, 'job_url': response.urljoin(detail_url)})

        # Go to the next page
        current_page = int(re.search(r'trang-(\d+)', response.url).group(1))
        next_page = current_page + 1
        next_page_url = response.url.replace(f'trang-{current_page}', f'trang-{next_page}')
        yield scrapy.Request(next_page_url, self.parse)

    def parse_job_details(self, response):
        title = response.css('body > main > section.search-result-list-detail.template-2 > div > div > div.col-12.mb-15 > section > div.apply-now-content > div.job-desc > h1::text').get(default='').strip()
        if not title:  # If title is empty, use the alternative structure
            title = response.css('body > main > section.template.template01 > div.top-template > div > div.head-template > div.head-left > div > h2::text').get(default='').strip()
            content_html = response.css('body > main > section.template.template01 > div.bottom-template > div > div > div.col-lg-9-custom > div.full-content > div:nth-child(1) > div').get(default='')
            company_name = response.css('body > main > section.template.template01 > div.top-template > div > div.head-template > div.head-left > a::text').get(default='').strip()
            company_url = response.css('body > main > section.template.template01 > div.top-template > div > div.head-template > div.head-left > a::attr(href)').get()
            yield response.follow(company_url, self.parse_company_location, meta={'response': response, 'title': title, 'content_html': content_html, 'company_name': company_name})
        else:
            self.extract_and_yield(response)

    def parse_company_location(self, response):
        original_response = response.meta['response']
        location = response.css('body > div.section-page.cp_basic_info > div > div > div.col-xs-12.col-sm-6.col-md-6.col-lg-6.cp_basic_info_details > ul > li:nth-child(1)::text').get(default='').strip()
        title = response.meta['title']
        content_html = response.meta['content_html']
        company_name = response.meta['company_name']

        content_selector = Selector(text=content_html)
        content = content_selector.xpath('string()').get().strip()

        experience = original_response.xpath('//*[@id="tab-1"]/section/div[1]/div/div[3]/div/ul/li[2]/p/text()').get(default='').strip()
        requirement_html = original_response.css('body > main > section.template.template01 > div.bottom-template > div > div > div.col-lg-9-custom > div.full-content > div:nth-child(2) > div > ul:nth-child(1)').get(default='')
        requirement_selector = Selector(text=requirement_html)
        requirement = requirement_selector.xpath('string()').get().strip()

        benefit_html = original_response.css('body > main > section.template.template01 > div.bottom-template > div > div > div.col-lg-9-custom > div.full-content > div:nth-child(2) > div > ul:nth-child(3)').get(default='')
        benefit_selector = Selector(text=benefit_html)
        benefit = benefit_selector.xpath('string()').get().strip()

        salary = original_response.xpath('//*[@id="tab-1"]/section/div[1]/div/div[3]/div/ul/li[1]/p/text()').get(default='').strip()
        skills_html = original_response.css('body > main > section.template.template01 > div.bottom-template > div > div > div.col-lg-9-custom > div.full-content > div.job-tags > ul').get(default='')
        skills_selector = Selector(text=skills_html)
        skills = skills_selector.xpath('string()').getall()

        yield {
            'title': title,
            'content': content,
            'company_name': company_name,
            'location': location,
            'experience': experience,
            'requirement': requirement,
            'benefit': benefit,
            'date_posted': original_response.meta['date_posted'],
            'source': 'careerviet.vn',
            'url': original_response.meta['job_url'],
            'salary': salary,
            'skills': ', '.join([skill.strip() for skill in skills])
        }

    def extract_and_yield(self, response):
        title = response.css('body > main > section.search-result-list-detail.template-2 > div > div > div.col-12.mb-15 > section > div.apply-now-content > div.job-desc > h1::text').get(default='').strip()
        content_html = response.css('#tab-1 > section > div.detail-row.reset-bullet > ul').get(default='')
        content_selector = Selector(text=content_html)
        content = content_selector.xpath('string()').getall()

        company_name = response.css('#tab-2 > section > div.company-introduction > div > div > div.img > div > a::text').get(default='').strip()
        location = response.xpath('//*[@id="tab-2"]/section/div[1]/div/div/div[2]/text()').get(default='').strip()
        experience = response.xpath('//*[@id="tab-1"]/section/div[1]/div/div[3]/div/ul/li[2]/p/text()').get(default='').strip()
        
        requirement_html = response.css('#tab-1 > section > div:nth-child(4) > ul').get(default='')
        requirement_selector = Selector(text=requirement_html)
        requirement = requirement_selector.xpath('string()').getall()

        benefit_html = response.css('#tab-1 > section > div:nth-child(4) > ul:nth-child(7)').get(default='')
        benefit_selector = Selector(text=benefit_html)
        benefit = benefit_selector.xpath('string()').getall()

        salary = response.xpath('//*[@id="tab-1"]/section/div[1]/div/div[3]/div/ul/li[1]/p/text()').get(default='').strip()
        
        skills_html = response.css('#tab-1 > section > div.job-tags > ul').get(default='')
        skills_selector = Selector(text=skills_html)
        skills = skills_selector.xpath('string()').getall()

        yield {
            'title': title,
            'content': '\n'.join([item.strip() for item in content]),
            'company_name': company_name,
            'location': location,
            'experience': experience,
            'requirement': '\n'.join([item.strip() for item in requirement]),
            'benefit': '\n'.join([item.strip() for item in benefit]),
            'date_posted': response.meta['date_posted'],
            'source': 'careerviet.vn',
            'url': response.meta['job_url'],
            'salary': salary,
            'skills': ', '.join([item.strip() for item in skills])
        }
