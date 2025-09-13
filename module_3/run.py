#!/usr/bin/env python3

import psycopg
import json
from app import create_app
from load_data import load_data_to_db, load_jsonl

# path to jsonl data from module 2
file_path = "data/llm_extend_applicant_data.jsonl"

# loads the initial module 2 data to the db, dropping the table if it already exists
load_data_to_db(file_path, initial_load=True)

app = create_app()  # create Flask app instance
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
