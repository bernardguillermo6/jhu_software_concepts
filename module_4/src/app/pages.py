"""
Flask blueprint for web routes.

Defines the main web routes for the Grad Cafe application:

- `/analysis` (alias `/`): Render SQL query results.
- `/scrape`: Scrape, pre-clean, and LLM-clean new entries.
- `/refresh_queries`: Load cleaned entries into PostgreSQL.
- `/scraper_status`: Return the scraper's busy/idle state.
"""

from flask import Blueprint, render_template
from src.scrape import scrape_new_entries
from src.clean import clean_data, clean_with_llm
import os, json
from src.load_data import load_data_to_db
from src.query_data import run_queries, get_max_id
from pathlib import Path

# Initialize blueprint
bp = Blueprint("pages", __name__)

# Global flag to track scraper state
is_scraping = False

ROOT_DIR = Path(__file__).resolve().parents[1]  # module_4
DATA_DIR = ROOT_DIR / "src" / "data"

@bp.route("/")
@bp.route("/analysis")
def index():
    """
    Render the index page with SQL query results and scraper status.

    Returns
    -------
    str
        Rendered HTML template for the index page.
    """
    global is_scraping
    data = run_queries()
    return render_template("pages/index.html", data=data, is_scraping=is_scraping)


@bp.route("/scrape", methods=["POST"])
def scrape():
    """
    Scrape, pre-clean, and LLM-clean new entries, then save to files.

    Workflow
    --------
    - Scrapes new survey entries (up to 20).
    - Saves raw entries to ``src/data/new_entries.json``.
    - Pre-cleans and saves to ``src/data/precleaned_entries.json``.
    - Runs LLM cleaning and saves to ``src/data/cleaned_entries.jsonl``.

    Returns
    -------
    tuple(dict, int)
        JSON response with status:
        - ``{"ok": True}, 200`` on success
        - ``{"busy": True}, 409`` if the scraper is already running
        - ``{"error": "..."} , 500`` if an exception occurs
    """
    global is_scraping
    if is_scraping:
        return {"busy": True}, 409

    is_scraping = True
    try:
        max_id = get_max_id()
        new_data = scrape_new_entries(max_id=max_id, target_count=1000)

        raw_file = os.path.join(DATA_DIR, "new_entries.json")
        with open(raw_file, "w") as f:
            json.dump(new_data, f, indent=2)

        precleaned_data = clean_data(new_data, target_count=1000)
        precleaned_file = os.path.join(DATA_DIR, "precleaned_entries.json")
        with open(precleaned_file, "w") as f:
            json.dump(precleaned_data, f, indent=2)

        cleaned_file = os.path.join(DATA_DIR, "cleaned_entries.jsonl")
        clean_with_llm(precleaned_file, output_file=cleaned_file)

        return {"ok": True}, 200
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        is_scraping = False


@bp.route("/refresh_queries", methods=["POST"])
def refresh_queries():
    """
    Load cleaned data into PostgreSQL and refresh SQL query answers.

    Returns
    -------
    tuple(dict, int)
        JSON response with status:
        - ``{"ok": True}, 200`` if refreshed successfully
        - ``{"busy": True}, 409`` if the scraper is already running
        - ``{"error": "..."} , 200`` if no cleaned file exists
        - ``{"error": "..."} , 500`` if loader fails
    """
    global is_scraping

    if is_scraping:
        return {"busy": True}, 409

    cleaned_file = os.path.join(DATA_DIR, "cleaned_entries.jsonl")
    if not os.path.exists(cleaned_file):
        return {"error": "No cleaned data file found. Please run scraper first."}, 200

    try:
        load_data_to_db(cleaned_file, initial_load=False)
        return {"ok": True}, 200
    except Exception as e:
        return {"error": str(e)}, 500


@bp.route("/scraper_status")
def scraper_status():
    """
    Return the current scraper status.

    Returns
    -------
    dict
        A JSON-compatible dictionary with key ``is_scraping`` (bool).
    """
    global is_scraping
    return {"is_scraping": is_scraping}
