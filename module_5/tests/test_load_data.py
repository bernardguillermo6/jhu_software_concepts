"""
Tests for the src.load_data module: database insertions, CLI entrypoints, and edge cases.
"""

import runpy
import sys
from unittest.mock import MagicMock

import pytest

import src.load_data as loader  # replace with actual filename if different


def make_fake_conn(monkeypatch):
    """
    Return a fake psycopg connection with cursor context manager,
    and patch psycopg.connect to use it.
    """

    class FakeCursor:
        """Stubbed psycopg cursor that records executed queries and params."""

        def __init__(self):
            """Initialize an empty query log."""
            self.queries = []
            self.params = []

        def __enter__(self):
            """Support context manager entry."""
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            """Support context manager exit (no cleanup)."""
            return False

        def execute(self, sql, params=None):
            """Record executed SQL and parameters."""
            self.queries.append(sql)
            self.params.append(params)

        def close(self):
            """No-op close for stub cursor."""
            return None

    class FakeConn:
        """Stubbed psycopg connection that provides a cursor and commit tracking."""

        def __init__(self):
            """Initialize with a fake cursor and commit flag."""
            self.cursor_obj = FakeCursor()
            self.committed = False

        def cursor(self):
            """Return the stub cursor."""
            return self.cursor_obj

        def commit(self):
            """Track when commit is called."""
            self.committed = True

        def __enter__(self):
            """Support context manager entry."""
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            """Support context manager exit (no cleanup)."""
            return False

    fake_conn = FakeConn()
    monkeypatch.setattr(loader.psycopg, "connect", lambda *a, **kw: fake_conn)
    return fake_conn


@pytest.mark.db
def test_insert_data_skips_rows_without_url(monkeypatch):
    """insert_data should skip rows that do not include a URL."""
    fake_conn = make_fake_conn(monkeypatch)

    # One row has url, one row does not
    data = [
        {"program": "CS", "URL": "http://example.com/1"},
        {"program": "Math"},  # missing URL
    ]

    loader.insert_data(fake_conn, data)

    # Only one query executed (the second row should be skipped)
    assert len(fake_conn.cursor_obj.queries) == 1
    assert "INSERT INTO applicants" in fake_conn.cursor_obj.queries[0]


@pytest.mark.db
def test_load_data_to_db_no_data(monkeypatch, capsys, tmp_path):
    """
    load_data_to_db should print a warning when the file is empty
    and no data is returned by load_jsonl.
    """
    # Write an empty file
    f = tmp_path / "empty.jsonl"
    f.write_text("")

    # Patch load_jsonl to simulate no data
    monkeypatch.setattr(loader, "load_jsonl", lambda _: [])

    loader.load_data_to_db(str(f), connection_string="fake://conn")

    captured = capsys.readouterr()
    assert f"No data found in {f}" in captured.out


@pytest.mark.integration
def test_cli_entrypoint_runs(monkeypatch, tmp_path, capsys):
    """
    Executing src/load_data.py as __main__ should perform an initial load
    when CLI args specify a file and --initial flag.
    """
    # Create a temp JSONL file with one row
    f = tmp_path / "data.jsonl"
    f.write_text('{"URL": "http://example.com/1", "program": "CS"}\n')

    # Patch psycopg connection
    make_fake_conn(monkeypatch)

    # Simulate CLI args: file + --initial
    testargs = ["prog", str(f), "--initial"]
    monkeypatch.setattr(sys, "argv", testargs)

    # Run the module as __main__
    runpy.run_module(loader.__name__, run_name="__main__")

    captured = capsys.readouterr()
    assert "Performing initial load" in captured.out
    assert "Loaded 1 entries" in captured.out


@pytest.mark.db
def test_load_data_to_db_appends(monkeypatch, tmp_path, capsys):
    """load_data_to_db should append entries when the --initial flag is not used."""
    f = tmp_path / "data.jsonl"
    f.write_text('{"URL": "http://example.com/append", "program": "CS"}\n')

    fake_conn = MagicMock()
    monkeypatch.setattr(loader.psycopg, "connect", lambda *a, **k: fake_conn)
    monkeypatch.setattr(loader, "insert_data", lambda conn, data: None)

    # Call without initial flag — should default to append branch
    loader.load_data_to_db(str(f), connection_string="fake://conn")

    captured = capsys.readouterr()
    assert "Appending new entries to existing table..." in captured.out
