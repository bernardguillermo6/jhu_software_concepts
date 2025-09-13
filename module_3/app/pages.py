from flask import Blueprint, render_template, redirect, url_for, flash
from module_2.scrape import scrape_new_entries
from module_2.clean import clean_data, clean_with_llm
import os, json, subprocess
from load_data import load_data_to_db
from query_data import get_db_connection, run_queries, get_max_id

# initializing the blueprint for the page routes
bp = Blueprint("pages", __name__)

# global flag to track scraper state
is_scraping = False

# route for the index page
@bp.route("/")
def index():
    global is_scraping
    data = run_queries()
    return render_template("pages/index.html", data=data, is_scraping=is_scraping)


# route for scraping, pre-cleaning, and LLM-cleaning new entries
@bp.route("/scrape", methods=["POST"])
def scrape():

    # set the scraping state. if the button is pushed, gives a message.
    global is_scraping
    if is_scraping:
        flash("Scraper is already running. Please wait.", "warning")
        return redirect(url_for("pages.index"))

    # if the Pull Data button is pushed, execute this path
    is_scraping = True
    try:
        max_id = get_max_id() # initialize the max id in the db
        new_data = scrape_new_entries(max_id=max_id, target_count=20) # scrape new entries

        # initialize the folder to store the new entries
        os.makedirs("data", exist_ok=True)

        # initialize the file where to store the new entries
        raw_file = os.path.join("data", "new_entries.json")
        with open(raw_file, "w") as f:
            json.dump(new_data, f, indent=2)

        # preclean and standardize the new entries and output to json
        precleaned_data = clean_data(new_data, target_count=20)
        precleaned_file = os.path.join("data", "precleaned_entries.json")
        with open(precleaned_file, "w") as f:
            json.dump(precleaned_data, f, indent=2)

        # take the precleaned entries and pass them through the LLM for normalization
        cleaned_file = os.path.join("data", "cleaned_entries.jsonl")
        clean_with_llm(precleaned_file, output_file=cleaned_file)

        flash(f"Scraper finished! {len(new_data)} new entries saved, pre-cleaned, and LLM-cleaned. Click Refresh Queries to update numbers.", "success")
    except Exception as e:
        flash(f"Error during scraping: {e}", "danger")
    finally:
        is_scraping = False # set the state to false so the buttons become usable again

    return redirect(url_for("pages.index"))


# route for refreshing SQL query answers
@bp.route("/refresh_queries", methods=["POST"])
def refresh_queries():

    global is_scraping

    # if the Pull Data button is pushed, the Update Analysis button is disabled
    if is_scraping:
        flash("Cannot refresh queries while scraper is running.", "warning")
        return redirect(url_for("pages.index"))

    # load cleaned data into postgres before rerunning queries
    cleaned_file = os.path.join("data", "cleaned_entries.jsonl")
    if os.path.exists(cleaned_file):
        load_data_to_db(cleaned_file, initial_load=False)
        flash("SQL query answers refreshed with latest data!", "success")
    else:
        flash("No cleaned data file found. Please run scraper first.", "warning")

    return redirect(url_for("pages.index"))

# route for tracking the scraper status
@bp.route("/scraper_status")
def scraper_status():
    global is_scraping
    return {"is_scraping": is_scraping}
