# tests/test_query_data.py
import io
import sys
import subprocess
import pytest
from unittest.mock import patch
import src.query_data as query_data
import src.db as db
import runpy

@pytest.mark.query
def test_query_data_main_prints(monkeypatch):
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

@pytest.mark.query
def test_main_cli_uses_fake_db_and_prints(monkeypatch):
    # --- Fake DB plumbing ---
    class FakeCursor:
        def __init__(self):
            self.i = 0
        def execute(self, _query):
            self.i += 1
        def fetchone(self):
            # Return a single-column tuple, like a DB row
            return (f"Fake answer {self.i}",)
        def close(self):
            pass

    class FakeConn:
        def cursor(self):
            return FakeCursor()
        def close(self):
            pass

    # Patch the connection factory that the module imports in main()/run_queries()
    monkeypatch.setattr(db, "get_db_connection", lambda: FakeConn())

    # Capture stdout
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)

    # Execute the module as __main__ so main() runs
    runpy.run_module("src.query_data", run_name="__main__", alter_sys=True)

    output = captured.getvalue()

    # Build expected questions from the module (not hitting the DB)
    expected_questions = [q for q, _ in query_data._get_questions_and_queries()]

    # Assert one Q/A pair per question, with separators
    for q in expected_questions:
        assert f"Q: {q}" in output
    assert output.count("A: ") == len(expected_questions)
    assert output.count("-" * 80) == len(expected_questions)