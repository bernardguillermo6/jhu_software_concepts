import pytest
from unittest.mock import MagicMock
from src import scrape


# --- _scrape_survey_page tests ---
@pytest.mark.analysis
def test_scrape_survey_page_valid(monkeypatch):
    """Covers the happy path where we parse an entry and badges."""
    html = """
    <table>
      <tr><td><a href="/result/123">Link</a></td><td></td><td>2025-09-18</td></tr>
      <tr>
        <td>
          <div class="tw-inline-flex">Fall 2025</div>
          <div class="tw-inline-flex">GRE 330</div>
          <div class="tw-inline-flex">GRE V 165</div>
          <div class="tw-inline-flex">GRE AW 4.5</div>
        </td>
      </tr>
    </table>
    """
    fake_resp = MagicMock(status=200, data=html.encode())
    monkeypatch.setattr(scrape.http, "request", lambda *a, **k: fake_resp)

    results = scrape._scrape_survey_page(1)
    assert len(results) == 1
    entry = results[0]
    assert entry["id"] == 123
    assert entry["term"] == "Fall 2025"
    assert entry["GRE Score"] == "330"
    assert entry["GRE V Score"] == "165"
    assert entry["GRE AW"] == "4.5"

@pytest.mark.analysis
def test_scrape_survey_page_request_exception(monkeypatch):
    """Covers exception in http.request (lines 16–18)."""
    def boom(*a, **k): raise Exception("network fail")
    monkeypatch.setattr(scrape.http, "request", boom)

    results = scrape._scrape_survey_page(1)
    assert results == []

@pytest.mark.analysis
def test_scrape_survey_page_non_200(monkeypatch):
    """Covers non-200 response (line 59)."""
    fake_resp = MagicMock(status=500, data=b"")
    monkeypatch.setattr(scrape.http, "request", lambda *a, **k: fake_resp)

    results = scrape._scrape_survey_page(1)
    assert results == []

@pytest.mark.analysis
def test_scrape_survey_page_no_link_tag(monkeypatch):
    """Covers path with no <a> tag (line 72)."""
    html = "<table><tr><td>No link here</td></tr></table>"
    fake_resp = MagicMock(status=200, data=html.encode())
    monkeypatch.setattr(scrape.http, "request", lambda *a, **k: fake_resp)

    results = scrape._scrape_survey_page(1)
    assert results == []

@pytest.mark.analysis
def test_scrape_survey_page_badge_unmatched(monkeypatch):
    """Covers badges with text that does not match GRE/Term (lines 54–55)."""
    html = """
    <table>
      <tr><td><a href="/result/300">Link</a></td><td></td><td>2025-09-18</td></tr>
      <tr><td><div class="tw-inline-flex">RandomText</div></td></tr>
    </table>
    """
    fake_resp = MagicMock(status=200, data=html.encode())
    monkeypatch.setattr(scrape.http, "request", lambda *a, **k: fake_resp)

    results = scrape._scrape_survey_page(1)
    assert len(results) == 1
    assert "term" not in results[0]
    assert "GRE Score" not in results[0]


# --- _scrape_page tests ---
@pytest.mark.analysis
def test_scrape_page_valid(monkeypatch):
    """Covers valid detailed page parsing."""
    html = """
    <dl>
      <div><dt>Program</dt><dd>CS</dd></div>
      <div><dt>Status</dt><dd>Accepted</dd></div>
    </dl>
    """
    fake_resp = MagicMock(status=200, data=html.encode())
    monkeypatch.setattr(scrape.http, "request", lambda *a, **k: fake_resp)

    entry = {"id": 42, "date_added": "2025-09-18", "term": "Fall 2025",
             "GRE Score": "330", "GRE V Score": "165", "GRE AW": "4.5"}
    result = scrape._scrape_page(entry)

    assert result["id"] == 42
    assert "Program" in result["data"]
    assert result["data"]["GRE Score"] == "330"

@pytest.mark.analysis
def test_scrape_page_non_200(monkeypatch):
    """Covers non-200 in _scrape_page."""
    fake_resp = MagicMock(status=404, data=b"")
    monkeypatch.setattr(scrape.http, "request", lambda *a, **k: fake_resp)

    result = scrape._scrape_page({"id": 999, "date_added": "x"})
    assert result is None

@pytest.mark.analysis
def test_scrape_page_exception(monkeypatch):
    """Covers exception in _scrape_page."""
    def boom(*a, **k): raise Exception("network fail")
    monkeypatch.setattr(scrape.http, "request", boom)

    result = scrape._scrape_page({"id": 100, "date_added": "x"})
    assert result is None


# --- scrape_new_entries tests ---
@pytest.mark.analysis
def test_scrape_new_entries_filters_and_stops(monkeypatch):
    """Covers scrape_new_entries filtering and stopping early."""
    # Fake survey page returns two entries
    monkeypatch.setattr(scrape, "_scrape_survey_page",
                        lambda page_num: [{"id": 1, "date_added": "2025-09-18"},
                                          {"id": 2, "date_added": "2025-09-18"}])
    # Fake detail returns entries as-is
    monkeypatch.setattr(scrape, "_scrape_page",
                        lambda entry: {"id": entry["id"], "url": "u", "data": {}})

    results = scrape.scrape_new_entries(max_id=1, target_count=2, batch_size=1)
    assert all(r["id"] > 1 for r in results)  # filtered by max_id

@pytest.mark.analysis
def test_scrape_survey_page_bad_href(monkeypatch):
    """Covers except Exception: pass in _scrape_survey_page."""
    html = """
    <table>
      <tr><td><a href='/result/notanumber'>bad</a></td><td>2025-09-18</td></tr>
    </table>
    """
    fake_resp = MagicMock(status=200, data=html.encode())
    monkeypatch.setattr(scrape.http, "request", lambda *a, **k: fake_resp)

    results = scrape._scrape_survey_page(1)
    # Exception in parsing -> caught and passed
    assert results == []

@pytest.mark.integration
def test_scrape_new_entries_no_new_entries(monkeypatch):
    """Covers 'No new entries found... break' in scrape_new_entries."""
    monkeypatch.setattr(scrape, "_scrape_survey_page", lambda page: [])
    monkeypatch.setattr(scrape, "_scrape_page", lambda entry: None)  # avoid detail scraping

    results = scrape.scrape_new_entries(target_count=2, batch_size=1)
    # Should stop early and return empty
    assert results == []    