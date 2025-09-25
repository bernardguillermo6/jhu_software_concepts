"""
Unit tests for src.clean.

Covers:
- parse_decision_date_for_test (wrapper around private parser).
- clean_data trimming, acceptance/rejection fields.
- clean_with_llm subprocess interactions (success/failure).
"""

import subprocess
from types import SimpleNamespace

import pytest
from src import clean
from src.clean import parse_decision_date_for_test


# ---------- parse_decision_date_for_test ----------

@pytest.mark.analysis
def test_parse_decision_date_for_test_cases():
    """Wrapper should delegate correctly and cover _parse_decision_date."""
    assert parse_decision_date_for_test("Notification sent on 12/03/2024") == "12/03/2024"
    assert parse_decision_date_for_test("Notification received recently") is None
    assert parse_decision_date_for_test("") is None
    assert parse_decision_date_for_test(None) is None


# ---------- clean_data ----------

def make_entry(program="CS", university="JHU", decision="Accepted", notification="15/04/2025"):
    """Helper to build a fake raw entry for clean_data tests."""
    return {
        "url": "http://example.com/1",
        "data": {
            "Program": f"<span>Program</span>{program}",
            "Institution": f"<span>Institution</span>{university}",
            "Decision": decision,
            "Notification": f"<span>Notification</span>{notification}",
        },
    }


@pytest.mark.analysis
def test_clean_data_acceptance_and_trim():
    """Acceptance case should populate acceptance_date and trim list length."""
    entries = [make_entry() for _ in range(5)]
    cleaned = clean.clean_data(entries, target_count=3)
    assert len(cleaned) == 3
    rec = cleaned[0]
    assert rec["program"].startswith("CS, JHU")
    assert rec["URL"] == "http://example.com/1"
    assert rec["acceptance_date"] == "15/04/2025"
    assert rec["rejection_date"] is None


@pytest.mark.analysis
def test_clean_data_rejection_and_other():
    """Rejected and waitlisted entries should map rejection/acceptance dates properly."""
    rejected = make_entry(decision="Rejected", notification="01/01/2024")
    other = make_entry(decision="Waitlisted", notification="02/02/2025")
    cleaned = clean.clean_data([rejected, other], target_count=5)

    assert len(cleaned) == 2
    rec_rej = cleaned[0]
    rec_other = cleaned[1]

    assert rec_rej["rejection_date"] == "01/01/2024"
    assert rec_rej["acceptance_date"] is None
    assert rec_other["acceptance_date"] is None
    assert rec_other["rejection_date"] is None



# ---------- clean_with_llm ----------

@pytest.mark.integration
def test_clean_with_llm_success(tmp_path, monkeypatch, capsys):
    """Simulate subprocess.run success and validate output parsing."""
    infile = tmp_path / "in.jsonl"
    outfile = tmp_path / "out.jsonl"
    infile.write_text('{"a": 1}\n')

    # Use SimpleNamespace instead of dummy class
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(returncode=0, stderr="")
    )

    outfile.write_text('{"program": "CS"}\n')
    data = clean.clean_with_llm(str(infile), str(outfile))
    captured = capsys.readouterr()
    assert "Cleaning entries with LLM" in captured.out
    assert data == [{"program": "CS"}]


@pytest.mark.integration
def test_clean_with_llm_failure(monkeypatch, tmp_path):
    """Simulate subprocess.run failure and assert RuntimeError raised."""
    infile = tmp_path / "in.jsonl"
    outfile = tmp_path / "out.jsonl"
    infile.write_text('{"x": 1}\n')

    # Use SimpleNamespace instead of dummy class
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(returncode=1, stderr="boom")
    )

    with pytest.raises(RuntimeError) as e:
        clean.clean_with_llm(str(infile), str(outfile))
    assert "LLM failed" in str(e.value)


@pytest.mark.analysis
def test_parse_decision_date_for_test_wrapper():
    """Wrapper should delegate to _parse_decision_date correctly."""
    assert parse_decision_date_for_test("Notification sent on 12/03/2024") == "12/03/2024"
    assert parse_decision_date_for_test("No date here") is None
