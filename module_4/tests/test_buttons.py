import pytest
from unittest.mock import patch


@pytest.mark.buttons
def test_pull_data_triggers_loader(client, monkeypatch, tmp_path):
    """
    POST /scrape should:
    - Return 200 with {"ok": True}.
    - Trigger the loader (scrape_new_entries, clean_data, clean_with_llm).
    """
    # ✅ Redirect DATA_DIR so /scrape writes to a safe temp dir
    monkeypatch.setattr("src.app.pages.DATA_DIR", tmp_path)

    with patch("src.app.pages.get_max_id", return_value=0):
        with patch("src.app.pages.scrape_new_entries", return_value=[{"id": 1, "question": "Q?", "answer": "A"}]) as mock_scrape:
            with patch("src.app.pages.clean_data", return_value=[{"id": 1, "question": "Q?", "answer": "A"}]) as mock_clean:
                with patch("src.app.pages.clean_with_llm", return_value=None) as mock_llm:
                    response = client.post("/scrape")
                    assert response.status_code == 200
                    assert response.json == {"ok": True}
                    mock_scrape.assert_called_once()
                    mock_clean.assert_called_once()
                    mock_llm.assert_called_once()


@pytest.mark.buttons
def test_update_analysis_when_not_busy(client, monkeypatch, tmp_path):
    """
    POST /refresh_queries should:
    - Return 200 with {"ok": True} when not busy.
    - Call load_data_to_db if cleaned_entries.jsonl exists.
    """
    # ✅ Redirect DATA_DIR so /refresh_queries sees a file
    monkeypatch.setattr("src.app.pages.DATA_DIR", tmp_path)
    (tmp_path / "cleaned_entries.jsonl").write_text("{}\n")

    with patch("src.app.pages.load_data_to_db", return_value=None) as mock_load:
        response = client.post("/refresh_queries")
        assert response.status_code == 200
        assert response.json == {"ok": True}
        mock_load.assert_called_once()


@pytest.mark.buttons
def test_update_analysis_no_file(client, monkeypatch, tmp_path):
    """
    POST /refresh_queries should:
    - Return 200 with an error message if cleaned_entries.jsonl does not exist.
    """
    monkeypatch.setattr("src.app.pages.DATA_DIR", tmp_path)  # empty dir
    response = client.post("/refresh_queries")
    assert response.status_code == 200
    assert "error" in response.json


@pytest.mark.buttons
def test_busy_gating_refresh_and_scrape(client):
    """
    When is_scraping=True:
    - POST /refresh_queries returns 409 with {"busy": True}.
    - POST /scrape returns 409 with {"busy": True}.
    """
    from src.app import pages

    # Force busy state
    pages.is_scraping = True

    resp_refresh = client.post("/refresh_queries")
    resp_scrape = client.post("/scrape")

    assert resp_refresh.status_code == 409
    assert resp_refresh.json == {"busy": True}

    assert resp_scrape.status_code == 409
    assert resp_scrape.json == {"busy": True}

    # Reset busy flag for other tests
    pages.is_scraping = False


@pytest.mark.buttons
def test_scrape_handles_exception(client):
    """
    If scrape_new_entries raises an exception:
    - POST /scrape should return 500 with {"error": "..."}.
    - is_scraping should reset to False.
    """
    from src.app import pages
    pages.is_scraping = False  # reset before test

    with patch("src.app.pages.get_max_id", return_value=0):
        with patch("src.app.pages.scrape_new_entries", side_effect=Exception("scrape failed")):
            response = client.post("/scrape")
            assert response.status_code == 500
            assert "error" in response.json

    assert pages.is_scraping is False


@pytest.mark.buttons
def test_refresh_queries_handles_loader_error(client, monkeypatch, tmp_path):
    """
    If load_data_to_db raises an exception:
    - POST /refresh_queries should return 500 with {"error": "..."}.
    """
    monkeypatch.setattr("src.app.pages.DATA_DIR", tmp_path)
    (tmp_path / "cleaned_entries.jsonl").write_text("{}\n")

    with patch("src.app.pages.load_data_to_db", side_effect=Exception("load failed")):
        response = client.post("/refresh_queries")
        assert response.status_code == 500
        assert "error" in response.json
