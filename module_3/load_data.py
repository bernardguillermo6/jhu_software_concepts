#!/usr/bin/env python3
import json
import psycopg
from pathlib import Path
import argparse

# dictionary to map jsonl keys to the column names in the db
KEY_MAP = {
    "program": "program",
    "comments": "comments",
    "date_added": "date_added",
    "URL": "url",
    "applicant_status": "status",
    "term": "term",
    "US/International": "us_or_international",
    "GPA": "gpa",
    "GRE Score": "gre",
    "GRE V Score": "gre_v",
    "GRE AW": "gre_aw",
    "Degree": "degree",
    "llm-generated-program": "llm_generated_program",
    "llm-generated-university": "llm_generated_university",
}


def load_jsonl(filename):
    """reads in a jsonl file"""
    
    with open(filename, "r") as f:
        return [json.loads(line) for line in f if line.strip()]


def create_table(conn):
    """create the postgres table"""

    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS applicants;")
        cur.execute("""
            CREATE TABLE applicants (
                p_id SERIAL PRIMARY KEY,
                program TEXT,
                comments TEXT,
                date_added DATE,
                url TEXT UNIQUE,
                status TEXT,
                term TEXT,
                us_or_international TEXT,
                gpa FLOAT,
                gre FLOAT,
                gre_v FLOAT,
                gre_aw FLOAT,
                degree TEXT,
                llm_generated_program TEXT,
                llm_generated_university TEXT
            );
        """)
        conn.commit()


def insert_data(conn, data):
    """insert a list of dictionaries to the postgres table"""
    
    with conn.cursor() as cur:
        for row in data:
            mapped_row = {KEY_MAP[k]: v for k, v in row.items() if k in KEY_MAP}

            if not mapped_row or "url" not in mapped_row:
                continue  # skip rows without a URL

            columns = ", ".join(mapped_row.keys())
            placeholders = ", ".join(f"%({k})s" for k in mapped_row.keys())
            sql = f"""
                INSERT INTO applicants ({columns})
                VALUES ({placeholders})
                ON CONFLICT (url) DO NOTHING;
            """
            cur.execute(sql, mapped_row)
        conn.commit()


def load_data_to_db(file_path, initial_load=False, connection_string=None):
    """load jsonl files into postgres"""
    
    # setting the connection string to db: thegradcafe
    connection_string = connection_string or "dbname=thegradcafe user=postgres host=localhost port=5432"

    # initialize the data from the jsonl file
    data = load_jsonl(file_path)
    if not data:
        print(f"No data found in {file_path}")
        return

    with psycopg.connect(connection_string) as conn:
        # if it's the first time the table is created, drop and recreate the table
        if initial_load:
            print("Performing initial load: dropping and recreating table...")
            create_table(conn)
        else:
            # if the table already exists, append new rows
            print("Appending new entries to existing table...")

        # insert the data into the table
        insert_data(conn, data)
        print(f"Loaded {len(data)} entries into the applicants table.")

def load_jsonl(filename="applicant_data.jsonl"):
    """load a jsonl file"""

    with open(filename, "r") as f:
        return [json.loads(line) for line in f if line.strip()]

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Load JSONL applicant data into PostgreSQL")
    parser.add_argument("file", help="Path to JSONL file")
    parser.add_argument("--initial", action="store_true", help="Drop table and reload all data")
    args = parser.parse_args()

    load_data_to_db(args.file, initial_load=args.initial)
