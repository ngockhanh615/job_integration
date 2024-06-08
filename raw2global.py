# import spacy
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

import re

# Load the Vietnamese SpaCy model
model = SentenceTransformer('keepitreal/vietnamese-sbert')

def clean_text(text):
    """Clean text to retain only words and numbers in Vietnamese."""
    text = re.sub(r'[^A-Za-zÀ-ỹ0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()

def get_embedding(text):
    """Get the embedding vector for a given text."""
    return model.encode(text)

def jaccard_similarity(list1, list2):
    """Compute Jaccard similarity between two lists."""
    set1 = set(list1)
    set2 = set(list2)
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union

def fetch_top_similar_embeddings(cursor, content_vector):
    """Fetch top 3 similar records based on content embeddings."""
    cursor.execute("""
        SELECT id, global_id, content_vector
        FROM embeddings
        ORDER BY content_vector <-> %s LIMIT 3
    """, (content_vector,))
    return cursor.fetchall()

def get_latest_raw_id(filepath):
    """Get the latest raw ID from the file."""
    latest_raw_id = 3000
    with open(filepath, "r") as file:
        lines = file.readlines()
        if lines:
            latest_raw_id = int(lines[-1].strip())
    return latest_raw_id

def save_latest_raw_id(filepath, raw_id):
    """Save the latest raw ID to the file."""
    with open(filepath, "a") as file:
        file.write('\n' + str(raw_id))

def insert_into_global_and_embeddings(cursor, record, content_vector):
    """Insert new record into global and embeddings tables."""
    title, content, company_name, location, experience, requirement, benefit, date_posted, source, url, skills, salary = record
    cursor.execute("""
        INSERT INTO global (title, content, company_name, location, experience, requirement, benefit, date_posted, source, url, skills, salary)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, (title, content, company_name, location, experience, requirement, benefit, date_posted, source, url, skills, salary))
    global_id = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO embeddings (global_id, content_vector)
        VALUES (%s, %s)
    """, (global_id, content_vector))

def process_new_records(cursor, new_records):
    """Process new records, check for duplicates, and insert if not a duplicate."""
    for new_record in new_records:
        raw_id, title, content, company_name, location, experience, requirement, benefit, date_posted, source, url, skills, salary = new_record
        print(f"Processing raw ID: {raw_id}")

        cleaned_title = clean_text(title)
        cleaned_content = clean_text(content)
        if not cleaned_title or not cleaned_content:
            print(f"Skipping raw ID: {raw_id} due to empty title or content")
            continue

        content_vector = get_embedding(cleaned_content)
        content_similar = fetch_top_similar_embeddings(cursor, content_vector)

        is_duplicate = False
        for content_sim in content_similar:
            _, global_id, content_vec = content_sim
            cursor.execute("SELECT title, content FROM global WHERE id = %s", (global_id,))
            global_title, global_content = cursor.fetchone()

            cleaned_global_title = clean_text(global_title)
            cleaned_global_content = clean_text(global_content)

            title_sim_value = jaccard_similarity(cleaned_title.split(), cleaned_global_title.split())
            if title_sim_value > 0.5:
                content_sim_value = jaccard_similarity(cleaned_content.split(), cleaned_global_content.split())
                if content_sim_value > 0.7:
                    is_duplicate = True
                    print(f"Duplicate found with global ID: {global_id} and raw ID: {raw_id}")
                    with open("/khanh/airflow/job_crawlers/log/duplicates.txt", "a") as file:
                        file.write(f"{raw_id}, {global_id}\n")
                    break

        if not is_duplicate:
            insert_into_global_and_embeddings(cursor, new_record[1:], content_vector)

def migrate_raw_to_global():
    """Migrate raw data to global data store."""
    conn = psycopg2.connect(
        dbname="jobs",
        user="postgres",
        password="postgres",
        host="10.100.21.125",
        port="5432"
    )
    cursor = conn.cursor()
    register_vector(cursor)
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()

    latest_raw_id = get_latest_raw_id("/khanh/airflow/job_crawlers/log/latest_raw_id.txt")
    cursor.execute("""
        SELECT id, title, content, company_name, location, experience, requirement, benefit, date_posted, source, url, skills, salary 
        FROM raw 
        WHERE id > %s 
        ORDER BY id
    """, (latest_raw_id,))
    new_records = cursor.fetchall()

    process_new_records(cursor, new_records)

    cursor.execute("SELECT max(id) FROM raw")
    latest_raw_id = cursor.fetchone()[0]
    save_latest_raw_id("/khanh/airflow/job_crawlers/log/latest_raw_id.txt", latest_raw_id)

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    migrate_raw_to_global()