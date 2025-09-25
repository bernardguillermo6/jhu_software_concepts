"""
Pytest fixtures and helpers for Flask client and pipeline tests.
"""

from unittest.mock import patch
import pytest
from src.app import create_app


# ------------------------
# Flask client fixture
# ------------------------

@pytest.fixture
def client():
    """Return a test client for the Flask app."""
    app = create_app()
    app.config.update({"TESTING": True})
    with app.test_client() as test_client:
        yield test_client


# ------------------------
# Shared test helpers
# ------------------------

def run_scrape_pipeline(test_client, monkeypatch, tmp_path):
    """Helper to simulate running the scrape pipeline with patched functions."""
    monkeypatch.setattr("src.app.pages.DATA_DIR", tmp_path)

    with patch("src.app.pages.get_max_id", return_value=0), \
         patch("src.app.pages.scrape_new_entries",
               return_value=[{"id": 1, "question": "Q?", "answer": "A"}]) as mock_scrape, \
         patch("src.app.pages.clean_data",
               return_value=[{"id": 1, "question": "Q?", "answer": "A"}]) as mock_clean, \
         patch("src.app.pages.clean_with_llm", return_value=None) as mock_llm:

        response = test_client.post("/scrape")
        return response, mock_scrape, mock_clean, mock_llm


def run_refresh_with_file(test_client):
    """Helper to simulate refresh with file present."""
    with patch("src.app.pages.load_data_to_db", return_value=None) as mock_load:
        response = test_client.post("/refresh_queries")
        return response, mock_load


def run_refresh_without_file(test_client):
    """Helper to simulate refresh without cleaned_entries.jsonl."""
    response = test_client.post("/refresh_queries")
    return response
