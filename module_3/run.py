#!/usr/bin/env python3

import psycopg
import json
from app import create_app
from load_data import load_data_to_db, load_jsonl

# Path to your JSONL file with pre-cleaned/LLM-cleaned data
file_path = "data/llm_extend_applicant_data.jsonl"

# Perform initial load: drops table if exists
load_data_to_db(file_path, initial_load=True)

app = create_app()  # create Flask app instance
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
