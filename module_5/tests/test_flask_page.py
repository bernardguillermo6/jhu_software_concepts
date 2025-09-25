"""
Unit tests for Flask app routes and index page rendering.
"""

import pytest
from flask import Flask

from src.app import create_app


@pytest.mark.web
def test_app_factory_registers_routes():
    """
    Ensure create_app builds a testable Flask app with required routes.
    """
    app = create_app()
    app.config.update({"TESTING": True})

    assert app is not None
    assert isinstance(app, Flask)

    url_map = [rule.rule for rule in app.url_map.iter_rules()]
    assert "/" in url_map
    assert "/analysis" in url_map


@pytest.mark.web
def test_index_page_renders(client):
    """
    GET / (analysis page) should return expected content.
    """
    response = client.get("/")
    assert response.status_code == 200

    html = response.data.decode()
    assert "Pull Data" in html
    assert "Update Analysis" in html
    assert "Analysis" in html
