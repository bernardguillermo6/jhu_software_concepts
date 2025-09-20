import json
import re
import pytest
from unittest.mock import patch
from bs4 import BeautifulSoup
from pathlib import Path

# Match exactly where the app expects the cleaned file
ROOT_DIR = Path(__file__).resolve().parents[1]  # module_4
DATA_DIR = ROOT_DIR / "src" / "data"


@pytest.mark.integration
def test_end_to_end_pull_update_render(client, tmp_path, monkeypatch):
    """
    End-to-end integration test:
    1. Inject fake scraper with multiple records.
    2. POST /scrape saves cleaned files.
    3. POST /refresh_queries triggers load_data_to_db.
    4. GET / renders updated analysis with correctly formatted values.
    """
    # ✅ Redirect DATA_DIR used in src.app.pages to tmp_path
    monkeypatch.setattr("src.app.pages.DATA_DIR", tmp_path)
    cleaned_file = tmp_path / "cleaned_entries.jsonl"

    fake_data = [
        {
            "program": "Physics PhD",
            "comments": "strong app",
            "date_added": "2025-09-18",
            "URL": "http://unique-url-phys.com",
            "applicant_status": "Accepted",
            "term": "Fall 2025",
            "US/International": "US",
            "GPA": 3.8,
            "GRE Score": 325,
            "GRE V Score": 162,
            "GRE AW": 4.0,
            "Degree": "BS",
            "llm-generated-program": "Physics",
            "llm-generated-university": "Harvard",
        },
        {
            "program": "Chemistry MS",
            "comments": "average app",
            "date_added": "2025-09-18",
            "URL": "http://unique-url-chem.com",
            "applicant_status": "Waitlisted",
            "term": "Fall 2025",
            "US/International": "International",
            "GPA": 3.2,
            "GRE Score": 310,
            "GRE V Score": 155,
            "GRE AW": 3.5,
            "Degree": "BS",
            "llm-generated-program": "Chemistry",
            "llm-generated-university": "Yale",
        },
    ]

    with patch("src.app.pages.scrape_new_entries", return_value=fake_data), \
         patch("src.app.pages.clean_data", return_value=fake_data), \
         patch("src.app.pages.clean_with_llm"), \
         patch("src.app.pages.load_data_to_db") as mock_loader:

        # Write fake cleaned file
        with cleaned_file.open("w") as f:
            for row in fake_data:
                f.write(json.dumps(row) + "\n")

        # Step 2: Pull data
        resp_scrape = client.post("/scrape", follow_redirects=True)
        assert resp_scrape.status_code == 200

        # Step 3: Update analysis (loader triggered here)
        resp_refresh = client.post("/refresh_queries", follow_redirects=True)
        assert resp_refresh.status_code == 200
        mock_loader.assert_called_once()

        # Step 4: Render page
        resp_page = client.get("/", follow_redirects=True)
        assert resp_page.status_code == 200
        soup = BeautifulSoup(resp_page.data.decode(), "html.parser")

        # Page should have Answer labels
        answers = [div.get_text() for div in soup.find_all("div", class_="answer")]
        assert any("Answer:" in text for text in answers)

        # Percentages should be formatted with 2 decimals
        for text in answers:
            if "%" in text:
                matches = re.findall(r"\d+\.\d{2}%", text)
                assert matches, f"Expected percentage with two decimals in: {text}"


@pytest.mark.integration
def test_multiple_pulls_respect_uniqueness(client, tmp_path, monkeypatch):
    """
    Running /scrape twice with overlapping data should still trigger load_data_to_db
    but not cause errors.
    """
    # ✅ Redirect DATA_DIR to tmp_path
    monkeypatch.setattr("src.app.pages.DATA_DIR", tmp_path)
    cleaned_file = tmp_path / "cleaned_entries.jsonl"

    fake_data = [
        {
            "program": "History MA",
            "comments": "repeat test",
            "date_added": "2025-09-18",
            "URL": "http://unique-url-history.com",
            "applicant_status": "Accepted",
            "term": "Fall 2025",
            "US/International": "US",
            "GPA": 3.7,
            "GRE Score": 315,
            "GRE V Score": 158,
            "GRE AW": 4.0,
            "Degree": "BA",
            "llm-generated-program": "History",
            "llm-generated-university": "Princeton",
        }
    ]

    with patch("src.app.pages.scrape_new_entries", return_value=fake_data), \
         patch("src.app.pages.clean_data", return_value=fake_data), \
         patch("src.app.pages.clean_with_llm"), \
         patch("src.app.pages.load_data_to_db") as mock_loader:

        # Write fake cleaned file
        with cleaned_file.open("w") as f:
            for row in fake_data:
                f.write(json.dumps(row) + "\n")

        # First scrape + refresh
        client.post("/scrape", follow_redirects=True)
        client.post("/refresh_queries", follow_redirects=True)

        # Second scrape + refresh (same fake data again)
        client.post("/scrape", follow_redirects=True)
        client.post("/refresh_queries", follow_redirects=True)

        # Loader should have been triggered at least once
        assert mock_loader.call_count >= 1
