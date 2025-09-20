import os
import json
import pytest
from unittest.mock import patch
from src.query_data import get_db_connection, run_queries
from src.load_data import create_table  # ✅ ensure schema creation

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "data")
DATA_DIR = os.path.abspath(DATA_DIR)


@pytest.mark.db
def test_insert_on_pull(client):
    """
    POST /scrape then /refresh_queries should insert rows into applicants.
    Ensures schema is created fresh for CI.
    """
    conn = get_db_connection()
    # ✅ Ensure schema exists before trying to insert
    create_table(conn)

    cur = conn.cursor()
    cur.execute("DELETE FROM applicants;")
    conn.commit()

    fake_data = [{
        "program": "CS PhD",
        "comments": "solid app",
        "date_added": "2025-09-18",
        "URL": "http://unique-url-1.com",  # KEY_MAP requires "URL"
        "applicant_status": "Accepted",
        "term": "Fall 2025",
        "US/International": "US",
        "GPA": 3.9,
        "GRE Score": 330,
        "GRE V Score": 165,
        "GRE AW": 4.5,
        "Degree": "BS",
        "llm-generated-program": "Computer Science",
        "llm-generated-university": "MIT"
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
    # ✅ Ensure schema exists
    create_table(conn)

    cur = conn.cursor()
    cur.execute("DELETE FROM applicants;")
    conn.commit()

    fake_data = [{
        "program": "Math MS",
        "comments": "dup test",
        "date_added": "2025-09-18",
        "URL": "http://unique-url-dup.com",  # unique URL
        "applicant_status": "Waitlisted",
        "term": "Fall 2025",
        "US/International": "International",
        "GPA": 3.5,
        "GRE Score": 320,
        "GRE V Score": 160,
        "GRE AW": 4.0,
        "Degree": "BS",
        "llm-generated-program": "Mathematics",
        "llm-generated-university": "Stanford"
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
    Ensures schema exists so CI won't fail if table is missing.
    """
    conn = get_db_connection()
    create_table(conn)  # ✅ make sure applicants table exists
    conn.close()

    results = run_queries()
    assert isinstance(results, list)
    if results:  # only check first row if not empty
        row = results[0]
        assert "question" in row
        assert "answer" in row

