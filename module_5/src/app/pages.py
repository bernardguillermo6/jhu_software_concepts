"""
Flask blueprint for web routes.

Defines the main web routes for the Grad Cafe application:

- `/analysis` (alias `/`): Render SQL query results.
- `/scrape`: Scrape, pre-clean, and LLM-clean new entries.
- `/refresh_queries`: Load cleaned entries into PostgreSQL.
- `/scraper_status`: Return the scraper's busy/idle state.
"""

#!/usr/bin/env python3
import json
from pathlib import Path

from flask import Blueprint, render_template

from src.clean import clean_data, clean_with_llm
from src.load_data import load_data_to_db
from src.query_data import get_max_id, run_queries
from src.scrape import scrape_new_entries

# Initialize blueprint
bp = Blueprint("pages", __name__)

# Scraper state stored in a dict (avoids `global`)
_scraper_state = {"running": False}

# Fix ROOT_DIR so it points to the project root (module_5)
ROOT_DIR = Path(__file__).resolve().parents[2]  # module_5
DATA_DIR = ROOT_DIR / "src" / "data"


@bp.route("/")
@bp.route("/analysis")
def index():
    """
    Render the index page with SQL query results and scraper status.
    """
    data = run_queries()
    return render_template(
        "pages/index.html", data=data, is_scraping=_scraper_state["running"]
    )


@bp.route("/scrape", methods=["POST"])
def scrape():
    """
    Scrape, pre-clean, and LLM-clean new entries, then save to files.
    """
    if _scraper_state["running"]:
        return {"busy": True}, 409

    _scraper_state["running"] = True
    try:
        max_id = get_max_id()
        new_data = scrape_new_entries(max_id=max_id, target_count=1000)

        raw_file = DATA_DIR / "new_entries.json"
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=2)

        precleaned_data = clean_data(new_data, target_count=1000)
        precleaned_file = DATA_DIR / "precleaned_entries.json"
        with open(precleaned_file, "w", encoding="utf-8") as f:
            json.dump(precleaned_data, f, indent=2)

        cleaned_file = DATA_DIR / "cleaned_entries.jsonl"
        clean_with_llm(precleaned_file, output_file=cleaned_file)

        return {"ok": True}, 200
    except (OSError, ValueError, RuntimeError) as e:
        return {"error": str(e)}, 500
    except Exception as e:  # pylint: disable=broad-exception-caught
        return {"error": str(e)}, 500
    finally:
        _scraper_state["running"] = False


@bp.route("/refresh_queries", methods=["POST"])
def refresh_queries():
    """
    Load cleaned data into PostgreSQL and refresh SQL query answers.
    """
    if _scraper_state["running"]:
        return {"busy": True}, 409

    cleaned_file = DATA_DIR / "cleaned_entries.jsonl"
    if not cleaned_file.exists():
        return {"error": "No cleaned data file found. Please run scraper first."}, 200

    try:
        load_data_to_db(str(cleaned_file), initial_load=False)
        return {"ok": True}, 200
    except (OSError, ValueError, RuntimeError) as e:
        return {"error": str(e)}, 500
    except Exception as e:  # pylint: disable=broad-exception-caught
        return {"error": str(e)}, 500


@bp.route("/scraper_status")
def scraper_status():
    """
    Return the current scraper status.
    """
    return {"is_scraping": _scraper_state["running"]}


# --- Scraper state helpers (public API for tests and internals) ---

def set_scraper_running(state: bool) -> None:
    """Set the scraper running flag."""
    _scraper_state["running"] = state


def is_scraper_running() -> bool:
    """Check whether the scraper is currently running."""
    return _scraper_state["running"]
