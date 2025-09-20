import os
import sys
import pytest
from pathlib import Path

# Always anchor relative to this file
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # module_4
sys.path.insert(0, str(PROJECT_ROOT))

from src.app import create_app, pages


@pytest.fixture
def client():
    """
    Provide a Flask test client for routes.

    - Calls create_app() with no arguments.
    - Updates config to enable TESTING mode.
    - Resets is_scraping before and after each test to avoid leakage.
    """
    app = create_app()
    app.config.update({"TESTING": True})

    # Reset busy flag before test
    pages.is_scraping = False

    with app.test_client() as client:
        yield client

    # Reset busy flag after test
    pages.is_scraping = False
