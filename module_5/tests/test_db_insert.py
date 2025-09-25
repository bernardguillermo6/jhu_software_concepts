"""Integration test ensuring scrape + refresh pipeline inserts data and triggers loader."""

def test_insert_and_refresh(client, mock_scrape_pipeline):
    """Integration test with pipeline fixture."""
    # Only mock_loader is needed; other values from the fixture are ignored
    _, _, mock_loader = mock_scrape_pipeline

    resp_scrape = client.post("/scrape")
    assert resp_scrape.status_code == 200

    resp_refresh = client.post("/refresh_queries")
    assert resp_refresh.status_code == 200

    mock_loader.assert_called_once()
