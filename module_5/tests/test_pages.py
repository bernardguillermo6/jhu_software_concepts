"""
Tests for the Flask blueprint routes defined in src.app.pages.
"""

import pytest
from src.app import pages


@pytest.mark.buttons
def test_scraper_status_returns_flag(client):
    """Test that /scraper_status correctly reflects the scraper state flag."""
    # Simulate active scraping
    pages.set_scraper_running(True)
    resp = client.get("/scraper_status")
    assert resp.status_code == 200
    assert resp.get_json() == {"is_scraping": True}

    # Simulate idle state
    pages.set_scraper_running(False)
    resp = client.get("/scraper_status")
    assert resp.status_code == 200
    assert resp.get_json() == {"is_scraping": False}


@pytest.mark.buttons
def test_scrape_handles_generic_exception(client, monkeypatch):
    """
    If scrape_new_entries raises a non-specific error,
    /scrape returns 500 from broad except.
    """
    monkeypatch.setattr("src.app.pages.get_max_id", lambda: 0)
    monkeypatch.setattr(
        "src.app.pages.scrape_new_entries",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("unexpected boom")),
    )
    resp = client.post("/scrape")
    assert resp.status_code == 500
    assert "error" in resp.json


@pytest.mark.buttons
def test_refresh_queries_handles_generic_exception(client, monkeypatch, tmp_path):
    """
    If load_data_to_db raises a non-specific error,
    /refresh_queries returns 500 from broad except.
    """
    monkeypatch.setattr("src.app.pages.DATA_DIR", tmp_path)
    (tmp_path / "cleaned_entries.jsonl").write_text("{}\n")

    monkeypatch.setattr(
        "src.app.pages.load_data_to_db",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("unexpected boom")),
    )
    resp = client.post("/refresh_queries")
    assert resp.status_code == 500
    assert "error" in resp.json


@pytest.mark.buttons
def test_is_scraper_running_helper_reflects_state():
    """Directly test the is_scraper_running() helper function."""
    pages.set_scraper_running(True)
    assert pages.is_scraper_running() is True

    pages.set_scraper_running(False)
    assert pages.is_scraper_running() is False
