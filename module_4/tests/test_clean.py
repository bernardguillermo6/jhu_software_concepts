import json
import subprocess
import pytest

import src.clean as clean


# ---------- _parse_decision_date ----------

@pytest.mark.analysis
def test_parse_decision_date_none_and_empty():
    assert clean._parse_decision_date(None) is None
    assert clean._parse_decision_date("") is None


@pytest.mark.analysis
def test_parse_decision_date_with_date():
    s = "Notification sent on 12/03/2024 via email"
    assert clean._parse_decision_date(s) == "12/03/2024"


@pytest.mark.analysis
def test_parse_decision_date_no_date():
    s = "Notification received recently"
    assert clean._parse_decision_date(s) is None


# ---------- clean_data ----------

def make_entry(program="CS", university="JHU", decision="Accepted", notification="15/04/2025"):
    """Helper to build a fake raw entry."""
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
    entries = [make_entry() for _ in range(5)]
    cleaned = clean.clean_data(entries, target_count=3)
    assert len(cleaned) == 3  # trimmed
    rec = cleaned[0]
    assert rec["program"].startswith("CS, JHU")
    assert rec["URL"] == "http://example.com/1"
    assert rec["acceptance_date"] == "15/04/2025"
    assert rec["rejection_date"] is None


@pytest.mark.analysis
def test_clean_data_rejection_and_other():
    rejected = make_entry(decision="Rejected", notification="01/01/2024")
    other = make_entry(decision="Waitlisted", notification="02/02/2025")
    cleaned = clean.clean_data([rejected, other], target_count=5)
    rec_rej, rec_other = cleaned
    assert rec_rej["rejection_date"] == "01/01/2024"
    assert rec_rej["acceptance_date"] is None
    assert rec_other["acceptance_date"] is None
    assert rec_other["rejection_date"] is None


# ---------- clean_with_llm ----------

@pytest.mark.integration
def test_clean_with_llm_success(tmp_path, monkeypatch, capsys):
    infile = tmp_path / "in.jsonl"
    outfile = tmp_path / "out.jsonl"
    infile.write_text('{"a": 1}\n')

    # Fake subprocess.run success
    class FakeResult:
        returncode = 0
        stderr = ""
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: FakeResult())

    # Create a fake output file
    outfile.write_text('{"program": "CS"}\n')

    data = clean.clean_with_llm(str(infile), str(outfile))
    captured = capsys.readouterr()
    assert "Cleaning entries with LLM" in captured.out
    assert data == [{"program": "CS"}]


@pytest.mark.integration
def test_clean_with_llm_failure(monkeypatch, tmp_path):
    infile = tmp_path / "in.jsonl"
    outfile = tmp_path / "out.jsonl"
    infile.write_text('{"x": 1}\n')

    class FakeResult:
        returncode = 1
        stderr = "boom"
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: FakeResult())

    with pytest.raises(RuntimeError) as e:
        clean.clean_with_llm(str(infile), str(outfile))
    assert "LLM failed" in str(e.value)
