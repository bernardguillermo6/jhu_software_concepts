#!/usr/bin/env python3

from module_2.utils import load_jsonl
import psycopg
import json
import pandas as pd
from sqlalchemy import create_engine
from app import create_app

# 1️⃣ Load JSONL file
def load_jsonl(filename):
    """Load a JSONL file into a list of dictionaries"""
    with open(filename, "r") as f:
        return [json.loads(line) for line in f if line.strip()]

data = load_jsonl("data/llm_extend_applicant_data.jsonl")

# 2️⃣ Map JSON keys to table columns
key_map = {
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
    "llm-generated-university": "llm_generated_university"
}

# 3️⃣ Connect to PostgreSQL
connection_string = "dbname=thegradcafe user=postgres host=localhost port=5432"

with psycopg.connect(connection_string) as conn:
    with conn.cursor() as cur:
        # 4️⃣ Drop the table if it exists
        cur.execute("DROP TABLE IF EXISTS applicants;")

        # 5️⃣ Create the table
        cur.execute("""
            CREATE TABLE applicants (
                p_id SERIAL PRIMARY KEY,
                program TEXT,
                comments TEXT,
                date_added DATE,
                url TEXT,
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

        # 6️⃣ Insert data
        for row in data:
            mapped_row = {key_map[k]: v for k, v in row.items() if k in key_map}

            if not mapped_row:
                continue  # skip rows with no relevant keys

            columns = ", ".join(mapped_row.keys())
            placeholders = ", ".join(f"%({k})s" for k in mapped_row.keys())
            sql = f"INSERT INTO applicants ({columns}) VALUES ({placeholders});"

            cur.execute(sql, mapped_row)


app = create_app()  # create Flask app instance
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)

import ipdb
ipdb.set_trace()
