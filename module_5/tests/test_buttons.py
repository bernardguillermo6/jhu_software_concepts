"""
Tests focused on verifying UI buttons and scraper/refresh POST routes.
"""

from unittest.mock import patch
import pytest
from bs4 import BeautifulSoup
from src.app import pages
from tests.conftest import run_scrape_pipeline, run_refresh_with_file


@pytest.mark.buttons
def test_buttons_are_present(client):
    """GET / should render 'Pull Data' and 'Update Analysis' buttons with stable IDs."""
    response = client.get("/")
    assert response.status_code == 200

    soup = BeautifulSoup(response.data.decode(), "html.parser")
    fetch_btn = soup.find("button", {"id": "fetch-btn"})
    refresh_btn = soup.find("button", {"id": "refresh-btn"})

    assert fetch_btn is not None and "Pull Data" in fetch_btn.get_text()
    assert refresh_btn is not None and "Update Analysis" in refresh_btn.get_text()


@pytest.mark.buttons
def test_pull_data_triggers_loader(client, monkeypatch, tmp_path):
    """POST /scrape should call scrape_new_entries, clean_data, and clean_with_llm."""
    response, mock_scrape, mock_clean, mock_llm = run_scrape_pipeline(client, monkeypatch, tmp_path)
    assert response.status_code == 200
    assert response.json == {"ok": True}
    mock_scrape.assert_called_once()
    mock_clean.assert_called_once()
    mock_llm.assert_called_once()


@pytest.mark.buttons
def test_update_analysis_when_not_busy(client):
    """POST /refresh_queries should succeed and call load_data_to_db if file exists."""
    response, mock_load = run_refresh_with_file(client)
    assert response.status_code == 200
    assert response.json == {"ok": True}
    mock_load.assert_called_once()


@pytest.mark.buttons
def test_update_analysis_no_file(client, monkeypatch):
    """POST /refresh_queries should return an error if file does not exist."""
    monkeypatch.setattr("pathlib.Path.exists", lambda self: False)
    resp = client.post("/refresh_queries")
    assert resp.status_code == 200
    assert "error" in resp.json


@pytest.mark.buttons
def test_busy_gating_refresh_and_scrape(client):
    """When is_scraping=True both refresh and scrape should return 409 busy."""
    pages.set_scraper_running(True)

    resp_refresh = client.post("/refresh_queries")
    resp_scrape = client.post("/scrape")

    assert resp_refresh.status_code == 409
    assert resp_refresh.json == {"busy": True}
    assert resp_scrape.status_code == 409
    assert resp_scrape.json == {"busy": True}

    pages.set_scraper_running(False)


@pytest.mark.buttons
def test_scrape_generic_exception(client, monkeypatch):
    """Force scrape() to raise a generic exception and verify 500 is returned."""
    monkeypatch.setattr("src.app.pages._scraper_state", {"running": False})
    with patch("src.app.pages.get_max_id", side_effect=Exception("boom")):
        resp = client.post("/scrape")
        assert resp.status_code == 500
        assert "boom" in resp.json["error"]


@pytest.mark.buttons
def test_refresh_generic_exception(client, monkeypatch):
    """Force refresh_queries() to raise a generic exception and verify 500 is returned."""
    # Pretend the cleaned file exists
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)

    with patch("src.app.pages.load_data_to_db", side_effect=Exception("kaboom")):
        resp = client.post("/refresh_queries")
        assert resp.status_code == 500
        assert "kaboom" in resp.json["error"]
