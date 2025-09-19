from flask import Blueprint, render_template
from src.scrape import scrape_new_entries
from src.clean import clean_data, clean_with_llm
import os, json
from src.load_data import load_data_to_db
from src.query_data import run_queries, get_max_id

# Initialize blueprint
bp = Blueprint("pages", __name__)

# Global flag to track scraper state
is_scraping = False

# Data directory inside src
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")  # src/data
DATA_DIR = os.path.abspath(DATA_DIR)  # resolve to absolute path
os.makedirs(DATA_DIR, exist_ok=True)  # make sure it exists


@bp.route("/")
@bp.route("/analysis")
def index():
    """Render the index page with SQL query results and scraper status.

    Output:
        str: Rendered HTML template for the index page.
    """
    global is_scraping
    data = run_queries()
    return render_template("pages/index.html", data=data, is_scraping=is_scraping)


@bp.route("/scrape", methods=["POST"])
def scrape():
    """Scrape, pre-clean, and LLM-clean new entries, then save to files.

    This route:
      - Scrapes new survey entries (up to 20).
      - Saves raw entries to `src/data/new_entries.json`.
      - Pre-cleans and saves to `src/data/precleaned_entries.json`.
      - Runs LLM cleaning and saves to `src/data/cleaned_entries.jsonl`.

    Output:
        JSON {ok: True} with 200 on success, or {busy: True} with 409 if busy.
    """
    global is_scraping
    if is_scraping:
        return {"busy": True}, 409

    is_scraping = True
    try:
        max_id = get_max_id()
        new_data = scrape_new_entries(max_id=max_id, target_count=20)

        raw_file = os.path.join(DATA_DIR, "new_entries.json")
        with open(raw_file, "w") as f:
            json.dump(new_data, f, indent=2)

        precleaned_data = clean_data(new_data, target_count=20)
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
    """Load cleaned data into PostgreSQL and refresh SQL query answers.

    Output:
        JSON {ok: True} with 200 on success,
        or {busy: True} with 409 if busy,
        or {error: "..."} with 200 if no file.
    """
    global is_scraping

    if is_scraping:
        return {"busy": True}, 409

    cleaned_file = os.path.join(DATA_DIR, "cleaned_entries.jsonl")
    if os.path.exists(cleaned_file):
        load_data_to_db(cleaned_file, initial_load=False)
        return {"ok": True}, 200
    else:
        return {"error": "No cleaned data file found. Please run scraper first."}, 200


@bp.route("/scraper_status")
def scraper_status():
    """Return the current scraper status.

    Output:
        dict: A json-compatible dictionary with key 'is_scraping' (bool).
    """
    global is_scraping
    return {"is_scraping": is_scraping}
