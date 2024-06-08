import scrapy
from parsel import Selector
from datetime import datetime, timedelta
import re

class TopcvSpider(scrapy.Spider):
    name = "topcv"
    allowed_domains = ["topcv.vn"]
    start_urls = ["https://www.topcv.vn/viec-lam-it?page=1"]

    def parse(self, response):
        # Get all job URLs on the current page
        job_urls = response.css('h3.title > a::attr(href)').extract()
        date_posted_selectors = response.css('#main > div.container.mt-24.bg-white.mb-40 > div.list-job > div.job-body.row > div.col-md-8 > div.job-list-2 > div > div > div.body > label')

        for i, job_url in enumerate(job_urls):
            date_posted_text = date_posted_selectors[i].css('::text').get()
            date_posted = self.parse_relative_date(date_posted_text)
            yield response.follow(job_url, self.parse_job_details, meta={'date_posted': date_posted, 'job_url': response.urljoin(job_url)})
        
        # Go to the next page
        next_page = response.css('#main > div.container.mt-24.bg-white.mb-40 > div.list-job > div.job-body.row > div.col-md-8 > div.text-center > nav > ul > li:nth-child(15) > a::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_job_details(self, response):
        # Extract job title from both the <a> tag and surrounding text within the <h1> element
        title_parts = response.css('h1.job-detail__info--title::text, h1.job-detail__info--title a::text').getall()
        title = ' '.join([t.strip() for t in title_parts if t.strip()])

        if not title:  # Check if title is empty, indicating a premium page
            title = response.css('h2.premium-job-basic-information__content--title::text').get(default='').strip()
            if not title:
                title = response.xpath('//*[@id="main"]/div[1]/div[2]/div/div/div[1]/div/div[1]/h2/text()').get(default='').strip()
                content_html = response.xpath('//*[@id="main"]/div[1]/div[2]/div/div/div[1]/div/div[2]/div[3]/div').get(default='')
                content_selector = Selector(text=content_html)
                content = content_selector.xpath('string()').get().strip()
                company_name = response.xpath('//*[@id="main"]/div[1]/div[2]/div/div/div[1]/div/div[2]/div[12]/a[2]/text()').get(default='').strip()
                location = response.xpath('//*[@id="main"]/div[1]/div[2]/div/div/div[1]/div/div[2]/div[2]/div/text()').get(default='').strip()
                experience = response.xpath('//*[@id="main"]/div[1]/div[2]/div/div/div[1]/div/div[2]/div[1]/div/div[6]/div[2]/span/text()').get(default='').strip()
                requirement_html = response.xpath('//*[@id="main"]/div[1]/div[2]/div/div/div[1]/div/div[2]/div[4]/div').get(default='')
                requirement_selector = Selector(text=requirement_html)
                requirement = requirement_selector.xpath('string()').get().strip()
                benefit_html = response.xpath('//*[@id="main"]/div[1]/div[2]/div/div/div[1]/div/div[2]/div[5]/div').get(default='')
                benefit_selector = Selector(text=benefit_html)
                benefit = benefit_selector.xpath('string()').get().strip()
            else:
                content_html = response.css('div.premium-job-description__box--content').get(default='')
                content_selector = Selector(text=content_html)
                content = content_selector.xpath('string()').get().strip()
                company_name = response.css('#premium-job > div.premium-job-header__company > div.premium-job-header__company--info > div.company-content__title > h1::text').get(default='').strip()
                location = response.xpath('//*[@id="premium-job"]/div[2]/div[1]/div[1]/div[3]/div[5]/div/div/text()').get(default='').strip()
                experience = response.css('#premium-job > div.premium-job-detail__left > div.premium-job-information > div.premium-job-basic-information__content > div.premium-job-basic-information__content--sections > div:nth-child(3) > div.basic-information-item__data--value::text').get(default='').strip()
                requirement_html = response.xpath('//*[@id="premium-job"]/div[2]/div[1]/div[1]/div[3]/div[3]/div').get(default='')
                requirement_selector = Selector(text=requirement_html)
                requirement = requirement_selector.xpath('string()').get().strip()
                benefit_html = response.xpath('//*[@id="premium-job"]/div[2]/div[1]/div[1]/div[3]/div[4]/div').get(default='')
                benefit_selector = Selector(text=benefit_html)
                benefit = benefit_selector.xpath('string()').get().strip()
        else:
            # Extract content and convert to plain text
            content_html = response.css('div.job-description__item--content').get(default='')
            content_selector = Selector(text=content_html)
            content = content_selector.xpath('string()').get().strip()
            company_name = response.css('h2.company-name-label > a::text').get(default='').strip()
            location = response.css('#box-job-information-detail > div.job-detail__information-detail--content > div > div:nth-child(4) > div > div::text').get(default='').strip()
            experience = response.css('#job-detail > div.job-detail__wrapper > div > div.job-detail__body-right > div.job-detail__box--right.job-detail__body-right--item.job-detail__body-right--box-general > div > div:nth-child(3) > div.box-general-group-info > div.box-general-group-info-value::text').get(default='').strip()
            requirement_html = response.xpath('//*[@id="box-job-information-detail"]/div[2]/div/div[2]/div').get(default='')
            requirement_selector = Selector(text=requirement_html)
            requirement = requirement_selector.xpath('string()').get().strip()
            benefit_html = response.xpath('//*[@id="box-job-information-detail"]/div[2]/div/div[3]/div').get(default='')
            benefit_selector = Selector(text=benefit_html)
            benefit = benefit_selector.xpath('string()').get().strip()
        
        # Clean the text fields
        content = self.clean_text(content)
        requirement = self.clean_text(requirement)
        benefit = self.clean_text(benefit)

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
            'url': response.meta['job_url']
        }

    def clean_text(self, text):
        """e
        Replace multiple spaces with a single space and ensure newlines are maintained.
        """
        return ' '.join(text.split()).replace(' . ', '. ').replace(' , ', ', ').replace(' ; ', '; ').replace(' : ', ': ').replace(' ! ', '! ').replace(' ? ', '? ')

    def parse_relative_date(self, date_text):
        """
        Parse relative date text like 'Cập nhật 1 ngày trước', 'Cập nhật 7 phút trước', etc. to an absolute datetime.
        """
        date_text = date_text.strip()
        now = datetime.now()

        if "phút" in date_text:
            minutes = int(re.search(r'(\d+)', date_text).group(1))
            return now - timedelta(minutes=minutes)
        elif "giờ" in date_text:
            hours = int(re.search(r'(\d+)', date_text).group(1))
            return now - timedelta(hours=hours)
        elif "ngày" in date_text:
            days = int(re.search(r'(\d+)', date_text).group(1))
            return now - timedelta(days=days)
        else:
            return now