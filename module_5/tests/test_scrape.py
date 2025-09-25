"""
Unit and integration tests for src.scrape.

Covers:
- scrape_new_entries (integration flow, edge cases, error handling)
- badge parsing in scrape_survey_page
- detail parsing in scrape_page
"""

from unittest.mock import MagicMock
import pytest
import urllib3

from src import scrape


@pytest.mark.analysis
def test_scrape_new_entries_valid(monkeypatch):
    """Happy path: fake scrape_survey_page and scrape_page to simulate one complete entry."""
    monkeypatch.setattr(
        scrape,
        "scrape_survey_page",
        lambda _n: [{"id": 123, "date_added": "2025-09-18", "term": "Fall 2025"}],
    )
    monkeypatch.setattr(
        scrape,
        "scrape_page",
        lambda entry: {
            "id": entry["id"],
            "url": f"https://thegradcafe.com/result/{entry['id']}",
            "data": {
                "Program": "CS",
                "Status": "Accepted",
                "Term": entry.get("term"),
                "GRE Score": "330",
                "GRE V Score": "165",
                "GRE AW": "4.5",
            },
        },
    )
    results = scrape.scrape_new_entries(target_count=1, batch_size=1)
    assert results and results[0]["data"]["Program"] == "CS"


# --- badge parsing ---
@pytest.mark.analysis
def test_scrape_survey_page_parses_term(monkeypatch):
    """Verify that a 'Fall 2025' badge is correctly extracted into the 'term' field."""
    html = """
    <table>
      <tr><td><a href="/result/10">Link</a></td><td></td><td>2025-09-18</td></tr>
      <tr><td><div class="tw-inline-flex">Fall 2025</div></td></tr>
    </table>
    """
    monkeypatch.setattr(
        scrape.http, "request",
        lambda *_a, **_k: MagicMock(status=200, data=html.encode())
    )
    results = scrape.scrape_survey_page(1)
    assert results[0]["term"] == "Fall 2025"


@pytest.mark.analysis
def test_scrape_survey_page_parses_gre_total(monkeypatch):
    """Verify that a 'GRE 330' badge is parsed as 'GRE Score'."""
    html = """
    <table>
      <tr><td><a href="/result/11">Link</a></td><td></td><td>2025-09-18</td></tr>
      <tr><td><div class="tw-inline-flex">GRE 330</div></td></tr>
    </table>
    """
    monkeypatch.setattr(
        scrape.http, "request",
        lambda *_a, **_k: MagicMock(status=200, data=html.encode())
    )
    results = scrape.scrape_survey_page(1)
    assert results[0]["GRE Score"] == "330"


@pytest.mark.analysis
def test_scrape_survey_page_parses_gre_v_and_aw(monkeypatch):
    """Verify that 'GRE V' and 'GRE AW' badges are parsed correctly."""
    html = """
    <table>
      <tr><td><a href="/result/12">Link</a></td><td></td><td>2025-09-18</td></tr>
      <tr>
        <td>
          <div class="tw-inline-flex">GRE V 165</div>
          <div class="tw-inline-flex">GRE AW 4.5</div>
        </td>
      </tr>
    </table>
    """
    monkeypatch.setattr(
        scrape.http, "request",
        lambda *_a, **_k: MagicMock(status=200, data=html.encode())
    )
    results = scrape.scrape_survey_page(1)
    assert results[0]["GRE V Score"] == "165"
    assert results[0]["GRE AW"] == "4.5"


# --- detail page parsing ---
@pytest.mark.analysis
def test_scrape_page_parses_and_merges_fields(monkeypatch):
    """Verify that detail pages with <dl> elements are parsed and merged with entry fields."""
    html = """
    <dl>
      <div><dt>Program</dt><dd>CS</dd></div>
      <div><dt>Status</dt><dd>Accepted</dd></div>
    </dl>
    """
    monkeypatch.setattr(
        scrape.http, "request",
        lambda *_a, **_k: MagicMock(status=200, data=html.encode())
    )
    entry = {
        "id": 55,
        "date_added": "2025-09-18",
        "term": "Fall 2025",
        "GRE Score": "330",
        "GRE V Score": "165",
        "GRE AW": "4.5",
    }
    result = scrape.scrape_page(entry)
    assert result["data"]["Program"] == "CS"
    assert result["data"]["GRE AW"] == "4.5"
    assert result["data"]["Term"] == "Fall 2025"


@pytest.mark.analysis
def test_scrape_page_non_200(monkeypatch):
    """Verify that a non-200 status returns None from scrape_page."""
    monkeypatch.setattr(
        scrape.http, "request",
        lambda *_a, **_k: MagicMock(status=500, data=b"")
    )
    result = scrape.scrape_page({"id": 999, "date_added": "2025-09-18"})
    assert result is None


@pytest.mark.analysis
def test_scrape_page_exception(monkeypatch):
    """Verify that an exception during http.request causes scrape_page to return None."""
    def boom(*_a, **_k):
        raise urllib3.exceptions.HTTPError("network exploded")
    monkeypatch.setattr(scrape.http, "request", boom)
    result = scrape.scrape_page({"id": 1000, "date_added": "2025-09-18"})
    assert result is None


# --- listing edge cases ---
@pytest.mark.analysis
def test_scrape_new_entries_no_link_tag(monkeypatch):
    """Verify that when a listing row has no <a> tag, no entries are returned."""
    html = "<table><tr><td>No link</td></tr></table>"
    monkeypatch.setattr(
        scrape.http, "request",
        lambda *_a, **_k: MagicMock(status=200, data=html.encode())
    )
    results = scrape.scrape_new_entries(target_count=1, batch_size=1)
    assert not results


@pytest.mark.analysis
def test_scrape_new_entries_bad_href(monkeypatch):
    """Verify that when a listing contains an invalid href, it is skipped."""
    html = "<table><tr><td><a href='/result/notanumber'>bad</a></td></tr></table>"
    monkeypatch.setattr(
        scrape.http, "request",
        lambda *_a, **_k: MagicMock(status=200, data=html.encode())
    )
    results = scrape.scrape_new_entries(target_count=1, batch_size=1)
    assert not results


@pytest.mark.analysis
def test_scrape_survey_page_exception(monkeypatch):
    """Verify that HTTPError exceptions in http.request return an empty list."""
    def boom(*_a, **_k):
        raise urllib3.exceptions.HTTPError("network down")
    monkeypatch.setattr(scrape.http, "request", boom)
    results = scrape.scrape_survey_page(1)
    assert not results


@pytest.mark.analysis
def test_scrape_new_entries_filters_by_max_id(monkeypatch):
    """Verify that scrape_new_entries filters out entries with id <= max_id."""
    monkeypatch.setattr(
        scrape,
        "scrape_survey_page",
        lambda _n: [{"id": 5, "date_added": "2025-09-18"}],
    )
    monkeypatch.setattr(
        scrape,
        "scrape_page",
        lambda entry: {"id": entry["id"], "url": "u", "data": {}},
    )
    results = scrape.scrape_new_entries(max_id=10, target_count=1, batch_size=1)
    assert not results


@pytest.mark.analysis
def test_scrape_survey_page_non_200(monkeypatch):
    """Verify that a non-200 status returns an empty list."""
    fake_resp = MagicMock(status=500, data=b"")
    monkeypatch.setattr(scrape.http, "request", lambda *_a, **_k: fake_resp)
    results = scrape.scrape_survey_page(1)
    assert not results


@pytest.mark.analysis
def test_scrape_new_entries_survey_page_exception(monkeypatch):
    """If scrape_survey_page raises an exception, scrape_new_entries should
    handle it and return [].
    """
    def boom(_n):
        raise RuntimeError("boom")
    monkeypatch.setattr(scrape, "scrape_survey_page", boom)
    monkeypatch.setattr(scrape, "scrape_page", lambda _e: None)
    results = scrape.scrape_new_entries(target_count=1, batch_size=1)
    assert results == []

@pytest.mark.analysis
def test_scrape_page_generic_exception(monkeypatch):
    """Verify that a non-HTTPError exception falls into the broad except and returns None."""
    def boom(*_a, **_k):
        raise ValueError("unexpected error")
    monkeypatch.setattr(scrape.http, "request", boom)
    result = scrape.scrape_page({"id": 2000, "date_added": "2025-09-18"})
    assert result is None
