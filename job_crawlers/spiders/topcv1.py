import scrapy
from datetime import datetime, timedelta
import re

class TopcvSpider(scrapy.Spider):
    name = "topcv1"
    allowed_domains = ["topcv.vn"]
    start_urls = ["https://www.topcv.vn/viec-lam-it?page=1"]

    custom_settings = {
        'RETRY_HTTP_CODES': [429],
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 0.5,
        'AUTOTHROTTLE_MAX_DELAY': 1.5,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 4,
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
        title = ' '.join([t.strip() for t in title_parts if t.strip() and re.search(r'\w', t)])

        if not title:
            title_parts = response.css('#main > div.section-job-detail > div.section-content-job-detail > div > div > div.col-md-7 > div > div.box-header > h2 *::text').getall()
            title = ' '.join([t.strip() for t in title_parts if t.strip() and re.search(r'\w', t)])
            content = self.extract_content(response, '#main > div.section-job-detail > div.section-content-job-detail > div > div > div.col-md-7 > div > div.box-job-info > div:nth-child(3) > div')
            company_name = response.css('#main > div.section-job-detail > div.section-content-job-detail > div > div > div.col-md-7 > div > div.box-job-info > div.box-seo-job-detail > a:nth-child(2)::text').get(default='').strip()
            location = response.css('#main > div.section-job-detail > div.section-content-job-detail > div > div > div.col-md-7 > div > div.box-job-info > div.box-address > div::text').get(default='').strip()
            experience = response.xpath('//*[@id="main"]/div[1]/div[2]/div/div/div[1]/div/div[2]/div[1]/div/div[6]/div[2]/span/text()').get(default='').strip()
            requirement = self.extract_content(response, '#main > div.section-job-detail > div.section-content-job-detail > div > div > div.col-md-7 > div > div.box-job-info > div:nth-child(4) > div')
            benefit = self.extract_content(response, '#main > div.section-job-detail > div.section-content-job-detail > div > div > div.col-md-7 > div > div.box-job-info > div:nth-child(5) > div')
            salary = response.css('#main > div.section-job-detail > div.section-content-job-detail > div > div > div.col-md-7 > div > div.box-job-info > div:nth-child(1) > div > div:nth-child(1) > div:nth-child(2) > span::text').get(default='').strip()
            skills = [x.strip() for x in response.css('#job-detail > div.job-detail__wrapper > div > div.job-detail__body-right > div.job-detail__box--right.job-detail__body-right--item.job-detail__body-right--box-category > div.box-category.collapsed > div.box-category-tags a::text').getall() if x.strip() and re.search(r'\w', x)]
            
            if not title:
                title = response.css('#premium-job > div.premium-job-detail.container > div.premium-job-detail__left > div.premium-job-information > div.premium-job-basic-information > div.premium-job-basic-information__content > h2::text').get(default='').strip()
                content = self.extract_content(response, '#premium-job > div.premium-job-detail.container > div.premium-job-detail__left > div.premium-job-information > div.premium-job-description > div:nth-child(1) > div')
                company_name = response.css('#premium-job > div.premium-job-header > div.premium-job-header__company.container > div.premium-job-header__company--info > div.company-content > div.company-content__title > h1::text').get(default='').strip()
                location = response.css('#premium-job > div.premium-job-detail.container > div.premium-job-detail__left > div.premium-job-information > div.premium-job-description > div:nth-child(4) > div > div::text').get(default='').strip()
                experience = response.css('#premium-job > div.premium-job-detail.container > div.premium-job-detail__left > div.premium-job-information > div.premium-job-basic-information > div.premium-job-basic-information__content > div.premium-job-basic-information__content--sections > div:nth-child(3) > div.basic-information-item__data > div.basic-information-item__data--value::text').get(default='').strip()
                requirement = self.extract_content(response, '#premium-job > div.premium-job-detail.container > div.premium-job-detail__left > div.premium-job-information > div.premium-job-description > div:nth-child(2) > div')
                benefit = self.extract_content(response, '#premium-job > div.premium-job-detail.container > div.premium-job-detail__left > div.premium-job-information > div.premium-job-description > div:nth-child(3) > div')
                salary = response.css('#premium-job > div.premium-job-detail.container > div.premium-job-detail__left > div.premium-job-information > div.premium-job-basic-information > div.premium-job-basic-information__content > div.premium-job-basic-information__content--sections > div:nth-child(1) > div.basic-information-item__data > div.basic-information-item__data--value::text').get(default='').strip()
        else:
            content = self.extract_content(response, '#box-job-information-detail > div.job-detail__information-detail--content > div > div:nth-child(1) > div')
            company_name = response.css('h2.company-name-label > a::text').get(default='').strip()
            location = response.css('#box-job-information-detail > div.job-detail__information-detail--content > div > div:nth-child(4) > div > div::text').get(default='').strip()
            experience = response.css('#job-detail > div.job-detail__wrapper > div > div.job-detail__body-right > div.job-detail__box--right.job-detail__body-right--item.job-detail__body-right--box-general > div > div:nth-child(3) > div.box-general-group-info > div.box-general-group-info-value::text').get(default='').strip()
            requirement = self.extract_content(response, '#box-job-information-detail > div.job-detail__information-detail--content > div > div:nth-child(2) > div')
            benefit = self.extract_content(response, '#box-job-information-detail > div.job-detail__information-detail--content > div.job-description > div:nth-child(3) > div')
            salary = response.css('#header-job-info > div.job-detail__info--sections > div:nth-child(1) > div.job-detail__info--section-content > div.job-detail__info--section-content-value::text').get(default='').strip()
            skills = [x.strip() for x in response.css('#job-detail > div.job-detail__wrapper > div > div.job-detail__body-right > div.job-detail__box--right.job-detail__body-right--item.job-detail__body-right--box-category > div.box-category.collapsed > div.box-category-tags a::text').getall() if x.strip() and re.search(r'\w', x)]

        if not title:
            title = ' '.join(x.strip() for x in response.xpath('//*[@id="premium-job"]/div[2]/div[1]/div[1]/div[1]/div[1]/h2//text()').extract() if x.strip() and re.search(r'\w', x))
        if not requirement:
            requirement = [x.strip() for x in response.xpath('/html/body/main/section[3]/div[2]/div/div/div[1]/div[3]/div[3]/div//text()').extract() if x.strip() and re.search(r'\w', x)]
        if not requirement:
            requirement = [x.strip() for x in response.css('#box-job-information-detail > div.job-detail__information-detail--content > div > div:nth-child(2) > div > ol > li::text').getall() if x.strip() and re.search(r'\w', x)]
        if not requirement:
            requirement = [x.strip() for x in response.xpath('//*[@id="premium-job"]/div[2]/div[1]/div[1]/div[3]/div[2]/div/ol/li//text()').extract() if x.strip() and re.search(r'\w', x)]
        if not requirement:
            requirement = [x.strip() for x in response.xpath('//*[@id="box-job-information-detail"]/div[2]/div/div[2]/div/ol/li//text()').extract() if x.strip() and re.search(r'\w', x)]
        if not requirement:
            requirement = [x.strip() for x in response.css('#box-job-information-detail > div.job-detail__information-detail--content > div > div:nth-child(3) > div > ol > li::text').getall() if x.strip() and re.search(r'\w', x)]
        if not requirement:
            requirement = [x.strip() for x in response.css('#box-job-information-detail > div.job-detail__information-detail--content > div > div:nth-child(2) > div > div::text').getall() if x.strip() and re.search(r'\w', x)]
        
        content = self.clean_text(content)
        requirement = self.clean_text(requirement)
        benefit = self.clean_text(benefit)
        skills = self.clean_text(skills)

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

    def extract_content(self, response, selector):
        content_div = response.css(selector)
        content = []
        if content_div:
            content += [p.xpath('string()').get().strip() for p in content_div.css('p')]
            content += [li.xpath('string()').get().strip() for ul in content_div.css('ul') for li in ul.css('li')]
        return content

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
