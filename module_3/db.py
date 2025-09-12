#!/usr/bin/env python3
import psycopg

def get_db_connection():
    return psycopg.connect(dbname="thegradcafe", user="postgres", host="localhost", port=5432)

def get_max_id():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(id), 0) FROM applicants")
            return cur.fetchone()[0]