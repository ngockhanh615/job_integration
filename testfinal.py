import spacy
import psycopg2
from pgvector.psycopg2 import register_vector
import numpy as np
import re
import time
import random

# Load the Vietnamese SpaCy model
nlp = spacy.load("vi_core_news_lg")

# Database connection
conn = psycopg2.connect(
    dbname="jobs",
    user="postgres",
    password="postgres",
    host="10.100.21.125",
    port="5432"
)
cursor = conn.cursor()

# Register pgvector
register_vector(cursor)

# Ensure the pgvector extension is enabled
cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
conn.commit()

# Function to clean text (retain words and numbers only in Vietnamese)
def clean_text(text):
    text = re.sub(r'[^A-Za-zÀ-ỹ0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()

# Function to get the embedding vector for a given text
def get_embedding(text):
    doc = nlp(text)
    return doc.vector

# Function to compute Jaccard similarity
def jaccard_similarity(list1, list2):
    set1 = set(list1)
    set2 = set(list2)
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union

# Function to fetch top 3 similar records based on embeddings
def fetch_top_similar_embeddings(title_vector, content_vector):
    cursor.execute("""
        SELECT id, global1_id, title_vector, content_vector
        FROM embeddings1
        ORDER BY title_vector <-> %s LIMIT 3
    """, (title_vector,))
    title_similar = cursor.fetchall()

    cursor.execute("""
        SELECT id, global1_id, title_vector, content_vector
        FROM embeddings1
        ORDER BY content_vector <-> %s LIMIT 3
    """, (content_vector,))
    content_similar = cursor.fetchall()

    return title_similar, content_similar

# Get latest raw_id from the last line of file
latest_raw_id = 0
with open("/khanh/airflow/latest_raw_id.txt", "r") as file:
    lines = file.readlines()
    if lines:
        latest_raw_id = int(lines[-1].strip())

# Fetch new records from the raw table
cursor.execute("SELECT id, title, content FROM raw WHERE source = 'topcv.vn' AND id > %s ORDER BY id", (latest_raw_id,))
new_records = cursor.fetchall()

for new_record in new_records:
    raw_id, title, content = new_record
    # if title is None or content is None:
    print(f"Processing raw ID: {raw_id}")

    # Clean and embed the title and content
    cleaned_title = clean_text(title)
    cleaned_content = clean_text(content)
    if cleaned_title is None or cleaned_content is None:
        print(f"Skipping raw ID: {raw_id}")
        continue
    # print("cleaned_title: ", cleaned_title)
    # print("cleaned_content: ", cleaned_content)
    title_vector = get_embedding(cleaned_title)
    content_vector = get_embedding(cleaned_content)

    # Fetch top 3 similar records
    title_similar, content_similar = fetch_top_similar_embeddings(title_vector, content_vector)

    # Check for similarity
    is_duplicate = False
    for title_sim in title_similar:
        _, global1_id, title_vec, _ = title_sim
        if raw_id == 3908:
            print("global: ", global1_id)
        title_sim_value = jaccard_similarity(cleaned_title.split(), clean_text(' '.join(map(str, title_vec))).split())
        if title_sim_value > 0.8:
            print('match title', global1_id, raw_id)
            for content_sim in content_similar:
                _, global1_id, _, content_vec = content_sim
                content_sim_value = jaccard_similarity(cleaned_content.split(), clean_text(' '.join(map(str, content_vec))).split())
                if content_sim_value > 0.8:
                    is_duplicate = True
                    break
            if is_duplicate:
                print(f"Duplicate found with global ID: {global1_id} and raw ID: {raw_id}")
                # Store to file
                with open("/khanh/airflow/duplicates.txt", "a") as file:
                    file.write(f"{raw_id}, {global1_id}\n")
                break

    # Insert into global and embeddings tables if not a duplicate
    if not is_duplicate:
        cursor.execute("""
            INSERT INTO global1 (title, content, source)
            VALUES (%s, %s, 'topcv.vn') RETURNING id
        """, (title, content))
        global1_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO embeddings1 (global1_id, title_vector, content_vector)
            VALUES (%s, %s, %s)
        """, (global1_id, title_vector, content_vector))

# Save latest raw_id to file
cursor.execute("SELECT max(id) FROM raw")
latest_raw_id = cursor.fetchone()[0]
with open("/khanh/airflow/latest_raw_id.txt", "a") as file:
    file.write('\n' + str(latest_raw_id))

conn.commit()
cursor.close()
conn.close()
