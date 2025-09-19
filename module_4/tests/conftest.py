import os
import sys
import pytest

# Ensure project root (module_4) is on sys.path so "src" is importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.app import create_app


@pytest.fixture
def client():
    """
    Provide a Flask test client for routes.
    
    - Calls create_app() with no arguments (matches your screenshot).
    - Updates config to enable TESTING mode.
    - Yields a test client that can call .get(), .post(), etc.
    """
    app = create_app()
    app.config.update({"TESTING": True})

    with app.test_client() as client:
        yield client
