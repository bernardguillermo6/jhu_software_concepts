from flask import Blueprint, render_template, redirect, url_for, flash
from module_2.scrape import scrape_new_entries
from module_2.clean import clean_data, clean_with_llm
import os, json, subprocess
from load_data import load_data_to_db
from query_data import get_db_connection, run_queries, get_max_id

# Initializing the blueprint for the page routes
bp = Blueprint("pages", __name__)

# Global flag to track scraper state
is_scraping = False


@bp.route("/")
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
      - Saves raw entries to `data/new_entries.json`.
      - Pre-cleans and saves to `data/precleaned_entries.json`.
      - Runs LLM cleaning and saves to `data/cleaned_entries.jsonl`.

    Output:
        A redirect to the index page.
    """
    global is_scraping
    if is_scraping:
        flash("Scraper is already running. Please wait.", "warning")
        return redirect(url_for("pages.index"))

    is_scraping = True
    try:
        max_id = get_max_id()
        new_data = scrape_new_entries(max_id=max_id, target_count=20)

        os.makedirs("data", exist_ok=True)

        raw_file = os.path.join("data", "new_entries.json")
        with open(raw_file, "w") as f:
            json.dump(new_data, f, indent=2)

        precleaned_data = clean_data(new_data, target_count=20)
        precleaned_file = os.path.join("data", "precleaned_entries.json")
        with open(precleaned_file, "w") as f:
            json.dump(precleaned_data, f, indent=2)

        cleaned_file = os.path.join("data", "cleaned_entries.jsonl")
        clean_with_llm(precleaned_file, output_file=cleaned_file)

        flash(
            f"Scraper finished! {len(new_data)} new entries saved, pre-cleaned, "
            "and LLM-cleaned. Click Refresh Queries to update numbers.",
            "success",
        )
    except Exception as e:
        flash(f"Error during scraping: {e}", "danger")
    finally:
        is_scraping = False

    return redirect(url_for("pages.index"))


@bp.route("/refresh_queries", methods=["POST"])
def refresh_queries():
    """Load cleaned data into PostgreSQL and refresh SQL query answers.

    Output:
        A redirect to the index page.
    """
    global is_scraping

    if is_scraping:
        flash("Cannot refresh queries while scraper is running.", "warning")
        return redirect(url_for("pages.index"))

    cleaned_file = os.path.join("data", "cleaned_entries.jsonl")
    if os.path.exists(cleaned_file):
        load_data_to_db(cleaned_file, initial_load=False)
        flash("SQL query answers refreshed with latest data!", "success")
    else:
        flash("No cleaned data file found. Please run scraper first.", "warning")

    return redirect(url_for("pages.index"))


@bp.route("/scraper_status")
def scraper_status():
    """Return the current scraper status.

    Output:
        dict: A json-compatible dictionary with key 'is_scraping' (bool).
    """
    global is_scraping
    return {"is_scraping": is_scraping}
