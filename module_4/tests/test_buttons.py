import pytest
from unittest.mock import patch


@pytest.mark.buttons
def test_pull_data_triggers_loader(client):
    """
    POST /scrape should:
    - Return 200 with {"ok": True}.
    - Trigger the loader (scrape_new_entries, clean_data, clean_with_llm).
    """
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
def test_update_analysis_when_not_busy(client):
    """
    POST /refresh_queries should:
    - Return 200 with {"ok": True} when not busy.
    - Call load_data_to_db if cleaned_entries.jsonl exists.
    """
    with patch("src.app.pages.os.path.exists", return_value=True):
        with patch("src.app.pages.load_data_to_db", return_value=None) as mock_load:
            response = client.post("/refresh_queries")
            assert response.status_code == 200
            assert response.json == {"ok": True}
            mock_load.assert_called_once()


@pytest.mark.buttons
def test_update_analysis_no_file(client):
    """
    POST /refresh_queries should:
    - Return 200 with an error message if cleaned_entries.jsonl does not exist.
    """
    with patch("src.app.pages.os.path.exists", return_value=False):
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
