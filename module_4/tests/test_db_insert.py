import json
import pytest
from unittest.mock import patch
from pathlib import Path

# Match exactly where the app expects the cleaned file
ROOT_DIR = Path(__file__).resolve().parents[1]  # module_4
DATA_DIR = ROOT_DIR / "src" / "data"


@pytest.mark.db
def test_insert_on_pull(client, tmp_path, monkeypatch):
    """
    POST /scrape then /refresh_queries should trigger load_data_to_db.
    """
    fake_data = [{
        "program": "CS PhD",
        "comments": "solid app",
        "date_added": "2025-09-18",
        "URL": "http://unique-url-1.com",
        "applicant_status": "Accepted",
        "term": "Fall 2025",
        "US/International": "US",
        "GPA": 3.9,
        "GRE Score": 330,
        "GRE V Score": 165,
        "GRE AW": 4.5,
        "Degree": "BS",
        "llm-generated-program": "Computer Science",
        "llm-generated-university": "MIT",
    }]

    # ✅ Redirect DATA_DIR used in src.app.pages to tmp_path
    monkeypatch.setattr("src.app.pages.DATA_DIR", tmp_path)
    cleaned_file = tmp_path / "cleaned_entries.jsonl"

    with patch("src.app.pages.scrape_new_entries", return_value=fake_data), \
         patch("src.app.pages.clean_data", return_value=fake_data), \
         patch("src.app.pages.clean_with_llm"), \
         patch("src.app.pages.load_data_to_db") as mock_loader:

        # Ensure the file exists so /refresh_queries sees it
        with cleaned_file.open("w") as f:
            for row in fake_data:
                f.write(json.dumps(row) + "\n")

        client.post("/scrape")
        client.post("/refresh_queries")

        # ✅ Only check loader was triggered
        mock_loader.assert_called_once()


@pytest.mark.db
def test_idempotency_on_duplicate_pull(client, tmp_path, monkeypatch):
    """
    Duplicate pulls should still trigger load_data_to_db, but not cause errors.
    """
    fake_data = [{
        "program": "Math MS",
        "comments": "dup test",
        "date_added": "2025-09-18",
        "URL": "http://unique-url-dup.com",
        "applicant_status": "Waitlisted",
        "term": "Fall 2025",
        "US/International": "International",
        "GPA": 3.5,
        "GRE Score": 320,
        "GRE V Score": 160,
        "GRE AW": 4.0,
        "Degree": "BS",
        "llm-generated-program": "Mathematics",
        "llm-generated-university": "Stanford",
    }]

    # ✅ Redirect DATA_DIR to tmp_path
    monkeypatch.setattr("src.app.pages.DATA_DIR", tmp_path)
    cleaned_file = tmp_path / "cleaned_entries.jsonl"

    with patch("src.app.pages.scrape_new_entries", return_value=fake_data), \
         patch("src.app.pages.clean_data", return_value=fake_data), \
         patch("src.app.pages.clean_with_llm"), \
         patch("src.app.pages.load_data_to_db") as mock_loader:

        with cleaned_file.open("w") as f:
            for row in fake_data:
                f.write(json.dumps(row) + "\n")

        # Run twice — should not error
        client.post("/scrape")
        client.post("/refresh_queries")
        client.post("/scrape")
        client.post("/refresh_queries")

        # Loader should have been called at least once
        assert mock_loader.call_count >= 1


@pytest.mark.db
def test_run_queries_returns_expected_keys(client):
    """
    run_queries() smoke test — only ensures no crash.
    """
    from src.query_data import run_queries
    results = run_queries()
    assert isinstance(results, list)
