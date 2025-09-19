import pytest
from src.app.pages import bp, is_scraping
from flask import Flask


@pytest.mark.web
def test_scraper_status_returns_flag(monkeypatch):
    # Create a Flask app and register the blueprint
    app = Flask(__name__)
    app.register_blueprint(bp)

    # Override is_scraping to True to simulate active scraping
    monkeypatch.setattr("src.app.pages.is_scraping", True)

    client = app.test_client()
    resp = client.get("/scraper_status")

    assert resp.status_code == 200
    assert resp.get_json() == {"is_scraping": True}

    # Now simulate not scraping
    monkeypatch.setattr("src.app.pages.is_scraping", False)
    resp = client.get("/scraper_status")

    assert resp.status_code == 200
    assert resp.get_json() == {"is_scraping": False}
