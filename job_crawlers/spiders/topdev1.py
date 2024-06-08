import scrapy
import json
from parsel import Selector
import re

class TopdevSpider(scrapy.Spider):
    name = "topdev1"
    allowed_domains = ["topdev.vn"]
    start_urls = ["https://api.topdev.vn/td/v2/jobs?fields[job]=id,slug,title,salary,company,extra_skills,skills_str,skills_arr,job_types_str,job_levels_arr,job_levels_ids,addresses,status_display,detail_url,job_url,salary,published,refreshed,requirements_arr,benefits,content,features&fields[company]=tagline,addresses,skills_arr,industries_arr,benefits&page=1&locale=vi_VN&ordering=jobs_new"]

    def parse(self, response):
        data = json.loads(response.body)
        for job in data.get('data', []):
            detail_url = job.get('detail_url')
            date_posted = job.get('refreshed', {}).get('datetime')
            skills = job.get('skills_arr', [])
            # salary in salary.value
            salary = job.get('salary', {}).get('value')
            requirement_raw = job.get('requirements_arr', [])
            requirement = []
            for req in requirement_raw:
                requirement.extend(req.get('value'))
            company = job.get('company', {})
            benefit_raw = company.get('benefits', [])
            benefit = [benefit.get('value') for benefit in benefit_raw]
            if detail_url:
                yield scrapy.Request(detail_url, self.parse_job_details, meta={'date_posted': date_posted, 'skills': skills, 'salary': salary, 'requirement': requirement, 'benefit': benefit})

        # Pagination
        current_page = int(response.url.split('page=')[-1].split('&')[0])
        next_page = current_page + 1
        if next_page > 100:
            return
        next_url = f"https://api.topdev.vn/td/v2/jobs?fields[job]=id,slug,title,salary,company,extra_skills,skills_str,skills_arr,job_types_str,job_levels_arr,job_levels_ids,addresses,status_display,detail_url,job_url,salary,published,refreshed,requirements_arr,benefits,content,features&fields[company]=tagline,addresses,skills_arr,industries_arr,benefits&page={next_page}&locale=vi_VN&ordering=jobs_new"
        yield scrapy.Request(next_url, self.parse)

    def parse_job_details(self, response):
        title = response.xpath('//*[@id="detailJobHeader"]/div[2]/h1/text()').get(default='').strip()
        content_html = response.xpath('//*[@id="JobDescription"]/div/div[@class="prose max-w-full text-sm text-black lg:text-base"]').get(default='')
        content_selector = Selector(text=content_html)
        content = content_selector.xpath('string()').get().strip()
        # content = response.xpath('//*[@id="JobDescription"]/div[1]/div/ol/li/span//text()').extract()
        # if not content:
        #     content = response.xpath('//*[@id="JobDescription"]/div[2]/div/ul/li/span//text()').extract()
        # if not content:
        #     content = [' '.join(response.xpath('//*[@id="JobDescription"]/div[2]/div/p//text()').extract())]
        company_name = response.xpath('//*[@id="detailJobHeader"]/div[2]/p/text()').get(default='').strip()
        location = response.xpath('//*[@id="detailJobHeader"]/div[2]/div[1]/div/div/text()').get(default='').strip()
        
        # Extract experience from the script tags
        script_contents = response.xpath('//script[contains(text(), "__next_f.push")]/text()').getall()
        experience = self.extract_experience_from_scripts(script_contents)

        # requirement_html = response.xpath('//*[@id="JobDescription"]/div[2]/div').get(default='')
        # requirement_selector = Selector(text=requirement_html)
        # requirement = requirement_selector.xpath('string()').get().strip()
        
        # benefit_html = response.xpath('//*[@id="JobDescription"]/div[4]/div').get(default='')
        # if not benefit_html:
        #     benefit_html = response.xpath('//*[@id="JobDescription"]/div[3]/div').get(default='')

        # benefit_selector = Selector(text=benefit_html)
        # benefit_items = benefit_selector.css('ul li::text').getall()
        # benefit = '\n'.join([item.strip() for item in benefit_items])
        requirement = response.meta['requirement'] if response.meta['requirement'] else ''
        
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
            'benefit': response.meta['benefit'] if response.meta['benefit'] else '',
            'date_posted': response.meta['date_posted'],
            'skills': response.meta['skills'],
            'source': 'topdev.vn',
            'url': response.url,
            'salary': response.meta['salary'] if response.meta['salary'] else '',
            'requirement': requirement
        }

    def extract_experience_from_scripts(self, script_contents):
        for script_content in script_contents:
            # Use regex to find the "experiences_str" field in the script content
            match = re.search(r'\\"experiences_str\\":\\"([^\\"]+)\\"', script_content)
            if match:
                return match.group(1).split(', ')[0]
        
        return ''
