import scrapy
from parsel import Selector
from datetime import datetime, timedelta
import re

class TopcvSpider(scrapy.Spider):
    name = "topcv"
    allowed_domains = ["topcv.vn"]
    start_urls = ["https://www.topcv.vn/viec-lam-it?page=1"]

    custom_settings = {
        'RETRY_TIMES': 10,
        'RETRY_HTTP_CODES': [429],
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 60,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'DOWNLOAD_DELAY': 3,
    }

    def parse(self, response):
        job_urls = response.css('h3.title > a::attr(href)').extract()
        date_posted_selectors = response.css('#main > div.container.mt-24.bg-white.mb-40 > div.list-job > div.job-body.row > div.col-md-8 > div.job-list-2 > div > div > div.body > label')

        for i, job_url in enumerate(job_urls):
            date_posted_text = date_posted_selectors[i].css('::text').get()
            date_posted = self.parse_relative_date(date_posted_text)
            yield response.follow(job_url, self.parse_job_details, meta={'date_posted': date_posted, 'job_url': response.urljoin(job_url)})
        
        next_page = response.css('#main > div.container.mt-24.bg-white.mb-40 > div.list-job > div.job-body.row > div.col-md-8 > div.text-center > nav > ul > li:nth-child(15) > a::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_job_details(self, response):
        title_parts = response.css('h1.job-detail__info--title::text, h1.job-detail__info--title a::text').getall()
        title = ' '.join([t.strip() for t in title_parts if t.strip()])

        if not title:
            title = response.css('h2.premium-job-basic-information__content--title::text').get(default='').strip()
            if not title:
                title = response.xpath('//*[@id="main"]/div[1]/div[2]/div/div/div[1]/div/div[1]/h2/text()').get(default='').strip()
                content_html = response.xpath('//*[@id="main"]/div[1]/div[2]/div/div/div[1]/div/div[2]/div[3]/div').get(default='')
                content_selector = Selector(text=content_html)
                content = content_selector.xpath('//li/text()').getall()
                company_name = response.xpath('//*[@id="main"]/div[1]/div[2]/div/div/div[1]/div/div[2]/div[12]/a[2]/text()').get(default='').strip()
                location = response.xpath('//*[@id="main"]/div[1]/div[2]/div/div/div[1]/div/div[2]/div[2]/div/text()').get(default='').strip()
                experience = response.xpath('//*[@id="main"]/div[1]/div[2]/div/div/div[1]/div/div[2]/div[1]/div/div[6]/div[2]/span/text()').get(default='').strip()
                requirement_html = response.xpath('//*[@id="main"]/div[1]/div[2]/div/div/div[1]/div/div[2]/div[4]/div').get(default='')
                requirement_selector = Selector(text=requirement_html)
                requirement = requirement_selector.xpath('//li/text()').getall()
                benefit_items = response.css('#box-job-information-detail > div.job-detail__information-detail--content > div.job-description > div:nth-child(3) > div > ul li::text').getall()
                benefit = ' '.join([item.strip() for item in benefit_items])
                salary = response.css('#header-job-info > div.job-detail__info--sections > div:nth-child(1) > div.job-detail__info--section-content > div.job-detail__info--section-content-value::text').get(default='').strip()
                skills = response.css('#job-detail > div.job-detail__wrapper > div > div.job-detail__body-right > div.job-detail__box--right.job-detail__body-right--item.job-detail__body-right--box-category > div.box-category.collapsed > div.box-category-tags a::text').getall()
            else:
                content_html = response.css('div.premium-job-description__box--content').get(default='')
                content_selector = Selector(text=content_html)
                content = content_selector.xpath('//li/text()').getall()
                company_name = response.css('#premium-job > div.premium-job-header__company > div.premium-job-header__company--info > div.company-content__title > h1::text').get(default='').strip()
                location = response.xpath('//*[@id="premium-job"]/div[2]/div[1]/div[1]/div[3]/div[5]/div/div/text()').get(default='').strip()
                experience = response.css('#premium-job > div.premium-job-detail__left > div.premium-job-information > div.premium-job-basic-information__content > div.premium-job-basic-information__content--sections > div:nth-child(3) > div.basic-information-item__data--value::text').get(default='').strip()
                requirement_html = response.xpath('//*[@id="premium-job"]/div[2]/div[1]/div[1]/div[3]/div[3]/div').get(default='')
                requirement_selector = Selector(text=requirement_html)
                requirement = requirement_selector.xpath('//li/text()').getall()
                benefit_items = response.css('#box-job-information-detail > div.job-detail__information-detail--content > div.job-description > div:nth-child(3) > div > ul li::text').getall()
                benefit = ' '.join([item.strip() for item in benefit_items])
                salary = response.css('#header-job-info > div.job-detail__info--sections > div:nth-child(1) > div.job-detail__info--section-content > div.job-detail__info--section-content-value::text').get(default='').strip()
                skills = response.css('#job-detail > div.job-detail__wrapper > div > div.job-detail__body-right > div.job-detail__box--right.job-detail__body-right--item.job-detail__body-right--box-category > div.box-category.collapsed > div.box-category-tags a::text').getall()
        else:
            content_html = response.css('div.job-description__item--content').get(default='')
            content_selector = Selector(text=content_html)
            content = content_selector.xpath('//li/text()').getall()
            company_name = response.css('h2.company-name-label > a::text').get(default='').strip()
            location = response.css('#box-job-information-detail > div.job-detail__information-detail--content > div > div:nth-child(4) > div > div::text').get(default='').strip()
            experience = response.css('#job-detail > div.job-detail__wrapper > div > div.job-detail__body-right > div.job-detail__box--right.job-detail__body-right--item.job-detail__body-right--box-general > div > div:nth-child(3) > div.box-general-group-info > div.box-general-group-info-value::text').get(default='').strip()
            requirement_html = response.xpath('//*[@id="box-job-information-detail"]/div[2]/div/div[2]/div').get(default='')
            requirement_selector = Selector(text=requirement_html)
            requirement = requirement_selector.xpath('//li/text()').getall()
            benefit_items = response.css('#box-job-information-detail > div.job-detail__information-detail--content > div.job-description > div:nth-child(3) > div > ul li::text').getall()
            benefit = ' '.join([item.strip() for item in benefit_items])
            salary = response.css('#header-job-info > div.job-detail__info--sections > div:nth-child(1) > div.job-detail__info--section-content > div.job-detail__info--section-content-value::text').get(default='').strip()
            skills = response.css('#job-detail > div.job-detail__wrapper > div > div.job-detail__body-right > div.job-detail__box--right.job-detail__body-right--item.job-detail__body-right--box-category > div.box-category.collapsed > div.box-category-tags a::text').getall()
        
        content = self.clean_text(content)
        requirement = self.clean_text(requirement)
        benefit = self.clean_text(benefit)
        skills = ', '.join(skills).strip()

        yield {
            'title': title,
            'content': content,
            'company_name': company_name,
            'location': location,
            'experience': experience,
            'requirement': requirement,
            'benefit': benefit,
            'date_posted': response.meta['date_posted'],
            'source': 'topcv.vn',
            'url': response.meta['job_url'],
            'salary': salary,
            'skills': skills
        }

    def clean_text(self, text):
        if isinstance(text, list):
            return [line.strip() for line in text if line.strip()]
        else:
            return ' '.join(text.split()).replace(' . ', '. ').replace(' , ', ', ').replace(' ; ', '; ').replace(' : ', ': ').replace(' ! ', '! ').replace(' ? ', '? ')

    def parse_relative_date(self, date_text):
        date_text = date_text.strip()
        now = datetime.now()

        if "phút" in date_text:
            minutes = int(re.search(r'(\d+)', date_text).group(1))
            return (now - timedelta(minutes=minutes)).strftime('%H:%M:%S %d-%m-%Y')
        elif "giờ" in date_text:
            hours = int(re.search(r'(\d+)', date_text).group(1))
            return (now - timedelta(hours=hours)).strftime('%H:%M:%S %d-%m-%Y')
        elif "ngày" in date_text:
            days = int(re.search(r'(\d+)', date_text).group(1))
            return (now - timedelta(days=days)).strftime('%H:%M:%S %d-%m-%Y')
        elif "tuần" in date_text:
            weeks = int(re.search(r'(\d+)', date_text).group(1))
            return (now - timedelta(weeks=weeks)).strftime('%H:%M:%S %d-%m-%Y')
        elif "tháng" in date_text:
            months = int(re.search(r'(\d+)', date_text).group(1))
            return (now - timedelta(days=30*months)).strftime('%H:%M:%S %d-%m-%Y')
        elif "năm" in date_text:
            years = int(re.search(r'(\d+)', date_text).group(1))
            return (now - timedelta(days=365*years)).strftime('%H:%M:%S %d-%m-%Y')
        else:
            return now.strftime('%H:%M:%S %d-%m-%Y')
