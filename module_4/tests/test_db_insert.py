import os
import json
import pytest
from unittest.mock import patch
from src.query_data import get_db_connection, run_queries

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "data")
DATA_DIR = os.path.abspath(DATA_DIR)


@pytest.mark.db
def test_insert_on_pull(client):
    """
    POST /scrape then /refresh_queries should insert rows into applicants.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM applicants;")
    conn.commit()

    fake_data = [{
        "program": "CS PhD",
        "comments": "solid app",
        "date_added": "2025-09-18",
        "url": "http://unique-url-1.com",   # matches DB column "url"
        "status": "Accepted",               # matches DB column "status"
        "term": "Fall 2025",
        "us_or_international": "US",        # matches DB column "us_or_international"
        "gpa": 3.9,
        "gre": 330,
        "gre_v": 165,
        "gre_aw": 4.5,
        "degree": "BS",
        "llm_generated_program": "Computer Science",
        "llm_generated_university": "MIT"
    }]

    cleaned_file = os.path.join(DATA_DIR, "cleaned_entries.jsonl")

    with patch("src.app.pages.scrape_new_entries", return_value=fake_data):
        with patch("src.app.pages.clean_data", return_value=fake_data):
            with patch("src.app.pages.clean_with_llm"):
                # Write test JSONL manually
                with open(cleaned_file, "w") as f:
                    for row in fake_data:
                        f.write(json.dumps(row) + "\n")

                client.post("/scrape")
                client.post("/refresh_queries")

    cur.execute("SELECT program, url, status FROM applicants;")
    rows = cur.fetchall()
    assert len(rows) >= 1
    for program, url, status in rows:
        assert program is not None
        assert url is not None
        assert status is not None

    conn.close()


@pytest.mark.db
def test_idempotency_on_duplicate_pull(client):
    """
    Duplicate pulls should not create duplicate rows (ON CONFLICT url).
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM applicants;")
    conn.commit()

    fake_data = [{
        "program": "Math MS",
        "comments": "dup test",
        "date_added": "2025-09-18",
        "url": "http://unique-url-dup.com",   # unique URL
        "status": "Waitlisted",
        "term": "Fall 2025",
        "us_or_international": "International",
        "gpa": 3.5,
        "gre": 320,
        "gre_v": 160,
        "gre_aw": 4.0,
        "degree": "BS",
        "llm_generated_program": "Mathematics",
        "llm_generated_university": "Stanford"
    }]

    cleaned_file = os.path.join(DATA_DIR, "cleaned_entries.jsonl")

    with patch("src.app.pages.scrape_new_entries", return_value=fake_data):
        with patch("src.app.pages.clean_data", return_value=fake_data):
            with patch("src.app.pages.clean_with_llm"):
                with open(cleaned_file, "w") as f:
                    for row in fake_data:
                        f.write(json.dumps(row) + "\n")

                client.post("/scrape")
                client.post("/refresh_queries")
                client.post("/scrape")
                client.post("/refresh_queries")

    cur.execute("SELECT COUNT(*) FROM applicants WHERE url = %s;", ("http://unique-url-dup.com",))
    count = cur.fetchone()[0]
    assert count == 1

    conn.close()


@pytest.mark.db
def test_run_queries_returns_expected_keys(client):
    """
    run_queries() should return dicts with 'question' and 'answer' keys.
    """
    results = run_queries()
    assert isinstance(results, list)
    if results:  # only check first row if not empty
        row = results[0]
        assert "question" in row
        assert "answer" in row
