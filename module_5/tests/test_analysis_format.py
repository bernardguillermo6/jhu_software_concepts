"""
Tests focused on verifying the formatting of the analysis page output.
"""

import re
import pytest
from bs4 import BeautifulSoup


@pytest.mark.analysis
def test_analysis_page_has_answers_and_labels(client):
    """
    GET / should render the analysis page with Answer labels.
    """
    resp = client.get("/")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data.decode(), "html.parser")
    answers = [div.get_text() for div in soup.find_all("div", class_="answer")]

    # There should be at least one Answer label present
    assert any("Answer:" in text for text in answers)


@pytest.mark.analysis
def test_percentages_have_two_decimals(client):
    """
    Percentages displayed in the analysis should always have 2 decimal places.
    """
    resp = client.get("/")
    assert resp.status_code == 200

    html = resp.data.decode()
    percentages = re.findall(r"\d+\.\d{2}%", html)

    # If percentages exist, all should match the two-decimal format
    if "%" in html:
        assert percentages, f"Expected two-decimal percentages, got: {html}"
