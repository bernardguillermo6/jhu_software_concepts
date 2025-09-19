import pytest
import re
from bs4 import BeautifulSoup


@pytest.mark.analysis
def test_answer_labels_present(client):
    """
    GET / should include 'Answer:' labels in the rendered HTML.
    Uses the real run_queries() output instead of fake data.
    """
    response = client.get("/")
    assert response.status_code == 200

    html = response.data.decode()
    assert "Answer:" in html  # page must include at least one Answer label


@pytest.mark.analysis
def test_percentages_two_decimals(client):
    """
    Ensure any percentages on the page are formatted with exactly two decimals.
    Uses the real run_queries() output instead of fake data.
    """
    response = client.get("/")
    assert response.status_code == 200

    soup = BeautifulSoup(response.data.decode(), "html.parser")
    answers = [div.get_text() for div in soup.find_all("div", class_="answer")]

    for text in answers:
        matches = re.findall(r"\d+\.\d{2}%", text)
        if "%" in text:  # only enforce on answers that are percentages
            assert matches, f"Expected percentage with two decimals in: {text}"
