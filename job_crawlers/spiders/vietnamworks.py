import scrapy
import json
from datetime import datetime
from parsel import Selector
from html import unescape

class VietnamworksSpider(scrapy.Spider):
    name = "vietnamworks"
    allowed_domains = ["vietnamworks.com"]
    start_urls = ["https://ms.vietnamworks.com/job-search/v1.0/search"]

    def start_requests(self):
        page = 1
        while True:
            if page == 200:
                break
            print(f"Scraping page {page}...")
            payload = {
                "userId": 0,
                "query": "",
                "filter": [
                    {
                        "field": "jobFunction",
                        "value": '[{"parentId":5,"childrenIds":[-1]}]'
                    }
                ],
                "hitsPerPage": 50,
                "order": [
                    {
                        "field": "approvedOn",
                        "value": "desc"
                    }
                ],
                "page": page,
                "ranges": [],
                "retrieveFields": [
                    "address",
                    "benefits",
                    "jobTitle",
                    "salaryMax",
                    "isSalaryVisible",
                    "jobLevelVI",
                    "isShowLogo",
                    "salaryMin",
                    "companyLogo",
                    "userId",
                    "jobLevel",
                    "jobLevelId",
                    "jobId",
                    "jobUrl",
                    "companyId",
                    "approvedOn",
                    "isAnonymous",
                    "alias",
                    "expiredOn",
                    "industries",
                    "workingLocations",
                    "services",
                    "companyName",
                    "salary",
                    "onlineOn",
                    "simpleServices",
                    "visibilityDisplay",
                    "isShowLogoInSearch",
                    "priorityOrder",
                    "skills",
                    "profilePublishedSiteMask",
                    "jobDescription",
                    "jobRequirement",
                    "prettySalary",
                    "requiredCoverLetter",
                    "languageSelectedVI",
                    "languageSelected",
                    "languageSelectedId"
                ]
            }

            headers = {
                "Content-Type": "application/json"
            }

            yield scrapy.Request(
                url=self.start_urls[0],
                method="POST",
                headers=headers,
                body=json.dumps(payload),
                callback=self.parse,
                meta={'page': page}
            )

            page += 1

    def parse(self, response):
        data = json.loads(response.body)

        # Check if data is empty to stop pagination
        if not data.get('data'):
            return

        for job in data['data']:
            jobUrl = job.get('jobUrl', '')
            date_posted = job.get('approvedOn', '')
            date_posted = self.convert_date_format(date_posted)
            if jobUrl:
                yield scrapy.Request(jobUrl, self.parse_job_details, meta={
                    'date_posted': date_posted,
                    'jobTitle': job.get('jobTitle', ''),
                    'jobDescription': self.extract_text_from_html(job.get('jobDescription', '')),
                    'companyName': job.get('companyName', ''),
                    'yearsOfExperience': job.get('yearsOfExperience', ''),
                    'jobRequirement': self.extract_text_from_html(job.get('jobRequirement', '')),
                    'benefits': ', '.join([benefit.get('benefitValue', '') for benefit in job.get('benefits', [])]),
                    'skills': ', '.join([skill.get('skillName', '') for skill in job.get('skills', [])]),
                    'salary': job.get('prettySalary', ''),
                    'source': 'vietnamworks',
                    'url': jobUrl
                })

    def parse_job_details(self, response):
        location = response.css('#vnwLayout__col > div > div.sc-37577279-0.joYsyf > div.sc-37577279-3.drWnZq > div > div:nth-child(1) > div:nth-child(2) > p::text').get(default='').strip()
        yield {
            'title': response.meta['jobTitle'],
            'content': response.meta['jobDescription'],
            'company_name': response.meta['companyName'],
            'location': location,
            'experience': f"{response.meta['yearsOfExperience']} năm",
            'requirement': response.meta['jobRequirement'],
            'benefit': response.meta['benefits'],
            'date_posted': response.meta['date_posted'],
            'source': response.meta['source'],
            'url': response.meta['url'],
            'skills': response.meta['skills'],
            'salary': response.meta['salary']
        }

    def convert_date_format(self, date_str):
        """
        Convert date from '2024-05-17T16:17:18+07:00' to '02:00:08 18-05-2024'.
        """
        dt = datetime.fromisoformat(date_str)
        return dt.strftime('%H:%M:%S %d-%m-%Y')

    def extract_text_from_html(self, html_content):
        """
        Extract text from HTML content.
        """
        selector = Selector(text=unescape(html_content))
        return selector.xpath('string()').get().strip()
