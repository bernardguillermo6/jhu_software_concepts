"""
Scraping logic for The Grad Cafe admissions survey.

This module is responsible for retrieving admissions data from
https://www.thegradcafe.com/survey. It includes:

- `scrape_survey_page`: Fetch and parse survey listing pages.
- `scrape_page`: Fetch and parse individual result detail pages.
- `scrape_new_entries`: Orchestrate scraping in batches, filter out
  already-seen entries, and return cleaned dictionaries.

The scraped data is later processed by `clean.py`.
"""

#!/usr/bin/env python3
import re
from concurrent.futures import ThreadPoolExecutor
import urllib3
from bs4 import BeautifulSoup

http = urllib3.PoolManager()


def _parse_badges_row(badges_row, term_pattern):
    """Parse GRE/term badges row into a dictionary."""
    record_data = {}
    for div in badges_row.find_all("div", class_="tw-inline-flex"):
        text = div.get_text(strip=True)
        if term_pattern.match(text):
            record_data["term"] = text
        elif text.startswith("GRE ") and not text.startswith(("GRE V", "GRE AW")):
            record_data["GRE Score"] = text.replace("GRE", "").strip()
        elif text.startswith("GRE V"):
            record_data["GRE V Score"] = text.replace("GRE V", "").strip()
        elif text.startswith("GRE AW"):
            record_data["GRE AW"] = text.replace("GRE AW", "").strip()
    return record_data


def _parse_entry_id_and_date(link_tag, date_tag):
    """Extract entry ID and date safely from HTML tags."""
    try:
        result_id = int(link_tag["href"].split("/result/")[1].split("#")[0])
        date_added = date_tag.get_text(strip=True) if date_tag else None
        return result_id, date_added
    except (ValueError, AttributeError, IndexError):
        return None, None


def scrape_survey_page(page_num: int):
    """
    Scrape the main survey page.

    Parameters
    ----------
    page_num : int
        The page number to scrape from https://www.thegradcafe.com/survey.

    Returns
    -------
    list of dict
        A list of entry dictionaries extracted from the survey page.
    """
    try:
        response = http.request(
            "GET", f"https://www.thegradcafe.com/survey/?page={page_num}", timeout=10.0
        )
        if response.status != 200:
            return []
    except urllib3.exceptions.HTTPError:
        return []

    soup = BeautifulSoup(response.data, "html.parser")
    entries = []
    rows = soup.select("tr")
    term_pattern = re.compile(
        r"^(Fall|Spring|Summer|Winter|F|S|Su|W)\s*\d{2,4}$", re.IGNORECASE
    )

    i = 0
    while i < len(rows):
        row = rows[i]
        link_tag = row.select_one("a[href^='/result/']")
        if not link_tag:
            i += 1
            continue

        badges_row = rows[i + 1] if i + 1 < len(rows) else None
        record_data = _parse_badges_row(badges_row, term_pattern) if badges_row else {}

        result_id, date_added = _parse_entry_id_and_date(
            link_tag, row.select_one("td:nth-child(3)")
        )
        if result_id:
            entry = {"id": result_id, "date_added": date_added}
            entry.update(record_data)
            entries.append(entry)

        i += 2

    return entries


def scrape_page(page_entry: dict):
    """
    Scrape the detailed results page for a single entry.

    Parameters
    ----------
    page_entry : dict
        A dictionary containing at least the ``id`` and ``date_added`` of the entry.

    Returns
    -------
    dict or None
        A dictionary with detailed scraped fields, or ``None`` if scraping fails.
    """
    page_id = page_entry["id"]
    url = f"https://www.thegradcafe.com/result/{page_id}"

    try:
        response = http.request("GET", url, timeout=10.0)
        if response.status != 200:
            return None

        soup = BeautifulSoup(response.data, "html.parser")
        pairs = {}
        for block in soup.select("dl > div"):
            dt = block.find("dt")
            dd = block.find("dd")
            if dt and dd:
                key = dt.get_text(strip=True)
                value = dd.get_text(strip=True)
                pairs[key] = value

        pairs["Date Added"] = page_entry["date_added"]
        pairs["Term"] = page_entry.get("term")
        pairs["GRE Score"] = page_entry.get("GRE Score")
        pairs["GRE V Score"] = page_entry.get("GRE V Score")
        pairs["GRE AW"] = page_entry.get("GRE AW")

        return {"id": page_id, "url": url, "data": pairs}
    except urllib3.exceptions.HTTPError:
        return None
    except Exception:  # pylint: disable=broad-exception-caught
        return None


def scrape_new_entries(max_id=None, target_count=30000, batch_size=5):
    """
    Scrape new survey entries from the site until a target count is reached.

    This function scrapes entries in batches of pages, filters out entries that
    are already known (based on ``max_id``), and then fetches detailed information
    for each entry.

    Parameters
    ----------
    max_id : int, optional
        The maximum existing entry ID in the database. Entries with IDs <= max_id
        will be ignored. Defaults to None.
    target_count : int, optional
        The total number of new entries to collect. Defaults to 30,000.
    batch_size : int, optional
        The number of pages to scrape in each batch. Defaults to 5.

    Returns
    -------
    list of dict
        A list of dictionaries containing the scraped entry details.
    """
    all_entries = []
    page_num = 1  # Initial page to start from

    while len(all_entries) < target_count:
        page_range = range(page_num, page_num + batch_size)
        print(f"Scraping survey pages {page_range[0]}–{page_range[-1]}...")

        with ThreadPoolExecutor(max_workers=100) as executor:
            try:
                results = list(executor.map(scrape_survey_page, page_range))
            except Exception:  # pylint: disable=broad-exception-caught
                results = [[]]

        batch_entries = [e for sublist in results for e in sublist]

        if max_id:
            batch_entries = [e for e in batch_entries if e["id"] > max_id]

        if not batch_entries:
            print("No new entries found in this batch. Stopping early.")
            break

        all_entries.extend(batch_entries)
        page_num += batch_size

    all_entries = all_entries[:target_count]
    print(f"Collected {len(all_entries)} survey entries. Fetching details...")

    with ThreadPoolExecutor(max_workers=300) as executor:
        detailed = list(executor.map(scrape_page, all_entries))

    return [d for d in detailed if d]
