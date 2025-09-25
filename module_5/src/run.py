"""
Application entrypoint for the Grad Cafe project.

This script:

- Loads applicant data from a JSONL file into the database.
- Creates a Flask web application instance via `app.create_app`.
- Runs the web server when executed directly.

Usage:
    python -m src.run
"""

#!/usr/bin/env python3
from pathlib import Path

from src.app import create_app
from src.load_data import load_data_to_db

# Path to jsonl data from module 2
FILE_PATH = Path("src") / "data" / "llm_extend_applicant_data.jsonl"

app = create_app()  # create Flask app instance

if __name__ == "__main__":
    load_data_to_db(FILE_PATH, initial_load=True)
    app.run(debug=True, host="0.0.0.0", port=8080)
