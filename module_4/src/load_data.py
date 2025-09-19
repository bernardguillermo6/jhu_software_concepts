#!/usr/bin/env python3
import json
import psycopg
from pathlib import Path
import argparse

# Dictionary to map jsonl keys to the column names in the db
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


def load_jsonl(filename: str):
    """Read data from a jsonl (json Lines) file.

    Input:
        filename (str): Path to the jsonl file.

    Output:
        list[dict]: A list of dictionaries, one per line of JSON in the file.
    """
    with open(filename, "r") as f:
        return [json.loads(line) for line in f if line.strip()]


def create_table(conn):
    """Create the PostgreSQL applicants table.

    Input:
        conn (psycopg.connection): A live PostgreSQL connection.

    Output:
        None. Commits the table creation to the database.
    """
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
    """Insert rows into the PostgreSQL 'applicants' table.

    Input:
        conn (psycopg.connection): A live postgreSQL connection.
        data (list[dict]): A list of dictionaries with applicant data,
            where keys correspond to jsonl keys and will be mapped to db columns.

    Output:
        None. Commits inserted rows into the database.
    """
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
    """Load applicant data from a JSONL file into PostgreSQL.

    Input:
        file_path (str): Path to the json file containing applicant data.
        initial_load (bool, optional): If True, drop and recreate the table
            before inserting. Defaults to False (append mode).
        connection_string (str, optional): A postgres connection string.
            If not provided, defaults to
            "dbname=thegradcafe user=postgres host=localhost port=5432".

    Output:
        None. Loads data into the applicants table.
    """
    connection_string = connection_string or "dbname=thegradcafe user=postgres host=localhost port=5432"

    # Initialize the data from the JSONL file
    data = load_jsonl(file_path)
    if not data:
        print(f"No data found in {file_path}")
        return

    with psycopg.connect(connection_string) as conn:
        if initial_load:
            print("Performing initial load: dropping and recreating table...")
            create_table(conn)
        else:
            print("Appending new entries to existing table...")

        insert_data(conn, data)
        print(f"Loaded {len(data)} entries into the applicants table.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load JSONL applicant data into PostgreSQL")
    parser.add_argument("file", help="Path to JSONL file")
    parser.add_argument("--initial", action="store_true", help="Drop table and reload all data")
    args = parser.parse_args()

    load_data_to_db(args.file, initial_load=args.initial)
