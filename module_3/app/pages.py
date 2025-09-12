from flask import Blueprint, render_template, redirect, url_for, flash, request
from db import get_db_connection
from module_2.scrape import scrape_new_entries
from module_2.clean import clean_data
import os, json, subprocess
from load_data import load_data_to_db

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
    """
    Calls the LLM on input_file and writes output to output_file.
    Returns the cleaned data as a Python list/dict.
    """
    print(f"Cleaning entries with LLM. Input: {input_file}, Output: {output_file}")
    cmd = [
        "python",
        "module_2/llm_hosting/app.py",
        "--file", input_file,
        "--out", output_file
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
    conn = get_db_connection()
    cur = conn.cursor()

    questions_and_queries = [
        ("How many entries do you have in your database who applied for Fall 2024?",
         "SELECT 'Applicant count: ' || COUNT(*) FROM applicants WHERE term in ('Fall 2024','F24')"),
        ("What percentage of entries are from international students (not American or Other) (to two decimal places)?",
         "SELECT 'Percent International: ' || ROUND((SUM(CASE WHEN us_or_international = 'International' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100), 2) || '%' AS percent_international FROM applicants;"),
        ("What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?",
         "SELECT 'Average GPA: ' || ROUND(AVG(NULLIF(gpa,0))::numeric,2) || ', Average GRE: ' || ROUND(AVG(NULLIF(gre,0))::numeric,2) || ', Average GRE V: ' || ROUND(AVG(NULLIF(gre_v,0))::numeric,2) || ', Average GRE AW: ' || ROUND(AVG(NULLIF(gre_aw,0))::numeric,2) FROM applicants;"),
        ("What is their average GPA of American students in Fall 2025?",
         "SELECT 'Average GPA American: ' || ROUND(AVG(NULLIF(gpa,0))::numeric,2) FROM applicants WHERE term = 'Fall 2025' AND us_or_international = 'American'"),
        ("What percent of entries for Fall 2025 are Acceptances (to two decimal places)?",
         "SELECT 'Acceptance percent: ' || ROUND(SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100,2) || '%' FROM applicants WHERE term = 'Fall 2025'"),
        ("What is the average GPA of applicants who applied for Fall 2025 who are Acceptances?",
         "SELECT 'Average GPA Acceptance: ' || ROUND(AVG(NULLIF(gpa,0))::numeric,2) FROM applicants WHERE term = 'Fall 2025' AND status = 'Accepted'"),
        ("How many entries are from applicants who applied to JHU for a masters degrees in Computer Science?",
         "SELECT 'JHU Computer Science Masters Applications: ' || COUNT(*) FROM applicants WHERE llm_generated_university = 'Johns Hopkins University' AND llm_generated_program = 'Computer Science' AND degree = 'Masters'"),
        ("How many entries from 2025 are acceptances from applicants who applied to Georgetown University for a PhD in Computer Science?",
         "SELECT 'Georgetown University Computer Science PhD Acceptances: ' || COUNT(*) FROM applicants WHERE llm_generated_university = 'Georgetown University' AND llm_generated_program = 'Computer Science' AND term LIKE '%2025%' AND status = 'Accepted' AND degree = 'PhD'")
    ]

    data = []
    for question, query in questions_and_queries:
        cur.execute(query)
        answer = cur.fetchone()[0]
        data.append({"question": question, "answer": answer})

    cur.close()
    conn.close()
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
        cleaned_data = clean_with_llm(precleaned_file, output_file=cleaned_file)

        load_data_to_db(cleaned_file, initial_load=False)

        flash(f"Scraper finished! {len(new_data)} new entries saved, pre-cleaned, LLM-cleaned, and loaded to DB.", "success")
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

    flash("SQL query answers refreshed!", "success")
    return redirect(url_for("pages.index"))


@bp.route("/scraper_status")
def scraper_status():
    global is_scraping
    return {"is_scraping": is_scraping}