from flask import Blueprint, render_template, redirect, url_for, flash
from module_2.scrape import scrape_new_entries
from module_2.clean import clean_data
import os, json, subprocess
from load_data import load_data_to_db
from query_data import get_db_connection, run_queries

# Initializing the blueprint for the page routes
bp = Blueprint("pages", __name__)

# Global flag to track scraper state
is_scraping = False


def get_max_id():
    """Fetch the current maximum ID from the applicants table."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT MAX(CAST(split_part(url, '/result/', 2) AS INTEGER)) AS max_id
        FROM applicants
    """)
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result if result else 0


def clean_with_llm(input_file: str, output_file: str):
    """Calls the LLM on input_file and writes output to output_file."""
    print(f"Cleaning entries with LLM. Input: {input_file}, Output: {output_file}")
    cmd = [
        "python",
        "module_2/llm_hosting/app.py",
        "--file", input_file,
        "--out", output_file,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"LLM failed: {result.stderr}")

    print(f"Finished cleaning with LLM. Output saved to: {output_file}")

    # Read JSONL back into Python objects
    with open(output_file) as f:
        cleaned_data = [json.loads(line) for line in f]

    return cleaned_data


# Route for the index page
@bp.route("/")
def index():
    global is_scraping
    data = run_queries()
    return render_template("pages/index.html", data=data, is_scraping=is_scraping)


# Route for scraping, pre-cleaning, and LLM-cleaning new entries
@bp.route("/scrape", methods=["POST"])
def scrape():
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

        flash(f"Scraper finished! {len(new_data)} new entries saved, pre-cleaned, and LLM-cleaned. Click Refresh Queries to update numbers.", "success")
    except Exception as e:
        flash(f"Error during scraping: {e}", "danger")
    finally:
        is_scraping = False

    return redirect(url_for("pages.index"))


# Route for refreshing SQL query answers
@bp.route("/refresh_queries", methods=["POST"])
def refresh_queries():
    global is_scraping
    if is_scraping:
        flash("Cannot refresh queries while scraper is running.", "warning")
        return redirect(url_for("pages.index"))

    # Load cleaned data into DB before re-running queries
    cleaned_file = os.path.join("data", "cleaned_entries.jsonl")
    if os.path.exists(cleaned_file):
        load_data_to_db(cleaned_file, initial_load=False)
        flash("SQL query answers refreshed with latest data!", "success")
    else:
        flash("No cleaned data file found. Please run scraper first.", "warning")

    return redirect(url_for("pages.index"))


@bp.route("/scraper_status")
def scraper_status():
    global is_scraping
    return {"is_scraping": is_scraping}
