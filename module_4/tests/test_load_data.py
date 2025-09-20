import io
import sys
import runpy
import pytest
from unittest.mock import MagicMock
import src.load_data as loader


import src.load_data as loader  # replace with actual filename if different


def make_fake_conn(monkeypatch):
    """Return a fake psycopg connection with cursor context manager."""
    class FakeCursor:
        def __init__(self):
            self.queries = []
            self.params = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

        def execute(self, sql, params=None):
            self.queries.append(sql)
            self.params.append(params)

        def close(self):
            pass

    class FakeConn:
        def __init__(self):
            self.cursor_obj = FakeCursor()
            self.committed = False

        def cursor(self):
            return self.cursor_obj

        def commit(self):
            self.committed = True

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    fake_conn = FakeConn()
    monkeypatch.setattr(loader.psycopg, "connect", lambda *a, **kw: fake_conn)
    return fake_conn


@pytest.mark.db
def test_insert_data_skips_rows_without_url(monkeypatch):
    fake_conn = make_fake_conn(monkeypatch)

    # One row has url, one row does not
    data = [
        {"program": "CS", "URL": "http://example.com/1"},
        {"program": "Math"}  # missing URL
    ]

    loader.insert_data(fake_conn, data)

    # Only one query executed (the second row should be skipped)
    assert len(fake_conn.cursor_obj.queries) == 1
    assert "INSERT INTO applicants" in fake_conn.cursor_obj.queries[0]


@pytest.mark.db
def test_load_data_to_db_no_data(monkeypatch, capsys, tmp_path):
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
    f = tmp_path / "data.jsonl"
    f.write_text('{"URL": "http://example.com/append", "program": "CS"}\n')

    fake_conn = MagicMock()
    monkeypatch.setattr(loader.psycopg, "connect", lambda *a, **k: fake_conn)
    monkeypatch.setattr(loader, "insert_data", lambda conn, data: None)

    # Call without initial flag — should default to append branch
    loader.load_data_to_db(str(f), connection_string="fake://conn")

    captured = capsys.readouterr()
    assert "Appending new entries to existing table..." in captured.out