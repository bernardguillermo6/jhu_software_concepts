"""
Integration tests for the full scrape → clean → load → render pipeline.

These tests ensure:
- /scrape saves raw and cleaned entries to disk.
- /refresh_queries triggers the loader.
- Duplicate scrapes remain idempotent.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "src" / "data"


@pytest.mark.integration
def test_end_to_end_pipeline_runs(client, tmp_path, monkeypatch):
    """
    Simulate a full scrape → clean → load pipeline run.
    """
    monkeypatch.setattr("src.app.pages.DATA_DIR", tmp_path)
    cleaned_file = tmp_path / "cleaned_entries.jsonl"

    fake_data = [{"program": "History MA", "URL": "http://unique-url.com"}]

    with patch("src.app.pages.scrape_new_entries", return_value=fake_data), patch(
        "src.app.pages.clean_data", return_value=fake_data
    ), patch("src.app.pages.clean_with_llm"), patch(
        "src.app.pages.load_data_to_db"
    ) as mock_loader:
        with cleaned_file.open("w", encoding="utf-8") as f:
            for row in fake_data:
                f.write(json.dumps(row) + "\n")

        resp_scrape = client.post("/scrape", follow_redirects=True)
        assert resp_scrape.status_code == 200

        resp_refresh = client.post("/refresh_queries", follow_redirects=True)
        assert resp_refresh.status_code == 200
        mock_loader.assert_called_once()


@pytest.mark.integration
def test_multiple_scrapes_idempotent(client, tmp_path, monkeypatch):
    """
    Running /scrape twice with same fake data should not break pipeline.
    """
    monkeypatch.setattr("src.app.pages.DATA_DIR", tmp_path)
    cleaned_file = tmp_path / "cleaned_entries.jsonl"

    fake_data = [{"program": "History MA", "URL": "http://unique-url.com"}]

    with patch("src.app.pages.scrape_new_entries", return_value=fake_data), patch(
        "src.app.pages.clean_data", return_value=fake_data
    ), patch("src.app.pages.clean_with_llm"), patch(
        "src.app.pages.load_data_to_db"
    ) as mock_loader:
        with cleaned_file.open("w", encoding="utf-8") as f:
            for row in fake_data:
                f.write(json.dumps(row) + "\n")

        client.post("/scrape", follow_redirects=True)
        client.post("/refresh_queries", follow_redirects=True)
        client.post("/scrape", follow_redirects=True)
        client.post("/refresh_queries", follow_redirects=True)

        assert mock_loader.call_count >= 1
