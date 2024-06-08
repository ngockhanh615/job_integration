# # Define your item pipelines here
# #
# # Don't forget to add your pipeline to the ITEM_PIPELINES setting
# # See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# # useful for handling different item types with a single interface
# from itemadapter import ItemAdapter


# class JobCrawlersPipeline:
#     def process_item(self, item, spider):
#         return item

import psycopg2
from datetime import datetime

class JobPipeline:
    def open_spider(self, spider):
        hostname = '10.100.21.125'
        username = 'postgres'  # replace with your username
        password = 'postgres'  # replace with your password
        database = 'jobs'
        self.connection = psycopg2.connect(
            host=hostname, user=username, password=password, dbname=database)
        self.cursor = self.connection.cursor()

    def close_spider(self, spider):
        self.cursor.close()
        self.connection.close()

    def process_item(self, item, spider):
        date_posted = datetime.strptime(item['date_posted'], '%H:%M:%S %d-%m-%Y')
        self.cursor.execute(
            "INSERT INTO raw (title, content, company_name, location, experience, requirement, benefit, date_posted, source, url, skills, salary) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (item['title'], item['content'], item['company_name'], item['location'], item['experience'], item['requirement'], item['benefit'], date_posted, item['source'], item['url'], item['skills'], item['salary']))
        self.connection.commit()
        return item
