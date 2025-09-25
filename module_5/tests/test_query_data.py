"""
Tests for the src.query_data module: CLI printing and DB integration.
"""

import io
import runpy
import sys
from unittest.mock import patch

import pytest

from src import db, query_data


@pytest.mark.db
def test_query_data_main_prints(monkeypatch):
    """main() should print Q/A pairs from run_queries()."""
    fake_data = [
        {"question": "What is 2+2?", "answer": "4"},
        {"question": "Square root of 9?", "answer": "3"},
    ]

    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)

    with patch("src.query_data.run_queries", return_value=fake_data):
        query_data.main()  # directly call main()

    output = captured.getvalue()
    assert "Q: What is 2+2?" in output
    assert "A: 4" in output
    assert "Q: Square root of 9?" in output
    assert "A: 3" in output


@pytest.mark.db
def test_main_cli_uses_fake_db_and_prints(monkeypatch):
    """Running module as __main__ should print expected Q/A pairs from fake DB."""

    class FakeCursor:
        """Stub cursor that fakes DB results for testing."""

        def __init__(self):
            """Track query count for predictable fake answers."""
            self.i = 0

        def __enter__(self):
            """Support `with` statement."""
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            """Support `with` statement cleanup."""
            return False  # don't suppress exceptions

        def execute(self, _query):
            """Increment query counter on execution."""
            self.i += 1

        def fetchone(self):
            """Return a tuple like a DB row with a fake answer."""
            return (f"Fake answer {self.i}",)

        def close(self):
            """No-op close."""
            return None

    class FakeConn:
        """Stub connection that returns a FakeCursor."""

        def cursor(self):
            """Return a new FakeCursor."""
            return FakeCursor()

        def close(self):
            """No-op close."""
            return None

    # Patch the connection factory
    monkeypatch.setattr(db, "get_db_connection", FakeConn)

    # Capture stdout
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)

    # Execute the module as __main__
    runpy.run_module("src.query_data", run_name="__main__", alter_sys=True)

    output = captured.getvalue()

    # Build expected questions
    expected_questions = [q for q, _ in query_data._get_questions_and_queries()]  # pylint: disable=W0212

    # Assert one Q/A pair per question, with separators
    for q in expected_questions:
        assert f"Q: {q}" in output
    assert output.count("A: ") == len(expected_questions)
    assert output.count("-" * 80) == len(expected_questions)
