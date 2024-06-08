# -*- coding: ascii -*-
import csv
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

# Read the CSV file
df = pd.read_csv('./district.csv', encoding='utf-8')
print(df.head())  # Display the first few rows of the DataFrame

# connect to postgres
# conn = psycopg2.connect(
#     host="10.100.21.125",
#     port="5432",
#     dbname="jobs",
#     user="postgres",
#     password="postgres"
# )

# uri conn
url = "postgresql://postgres:postgres@10.100.21.125:5432/jobs"
db = create_engine(url)
conn = db.connect()

# Create a cursor object using the cursor() method
# cursor = conn.cursor()
# insert df to table district
df.to_sql('district', con=conn, if_exists='replace', index=False)
conn.close()