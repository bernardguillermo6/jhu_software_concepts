"""
Scraping logic for The Grad Cafe admissions survey.

This module is responsible for retrieving admissions data from
https://www.thegradcafe.com/survey. It includes:

- `_scrape_survey_page`: Fetch and parse survey listing pages.
- `_scrape_page`: Fetch and parse individual result detail pages.
- `scrape_new_entries`: Orchestrate scraping in batches, filter out
  already-seen entries, and return cleaned dictionaries.

The scraped data is later processed by `clean.py`.
"""

#!/usr/bin/env python3
import urllib3
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import re

http = urllib3.PoolManager()


def _scrape_survey_page(page_num: int):
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
    url = f"https://www.thegradcafe.com/survey/?page={page_num}"
    try:
        response = http.request("GET", url, timeout=10.0)
        if response.status != 200:
            return []
    except Exception:
        return []

    soup = BeautifulSoup(response.data, "html.parser")
    entries = []

    rows = soup.select("tr")
    term_pattern = re.compile(r"^(Fall|Spring|Summer|Winter|F|S|Su|W)\s*\d{2,4}$", re.IGNORECASE)

    i = 0
    while i < len(rows):
        row = rows[i]
        link_tag = row.select_one("a[href^='/result/']")
        if link_tag:
            main_row = row
            badges_row = rows[i + 1] if i + 1 < len(rows) else None
            record_data = {}

            if badges_row:
                for div in badges_row.find_all("div", class_="tw-inline-flex"):
                    text = div.get_text(strip=True)
                    if term_pattern.match(text):
                        record_data["term"] = text
                    elif text.startswith("GRE ") and not text.startswith("GRE V") and not text.startswith("GRE AW"):
                        record_data["GRE Score"] = text.replace("GRE", "").strip()
                    elif text.startswith("GRE V"):
                        record_data["GRE V Score"] = text.replace("GRE V", "").strip()
                    elif text.startswith("GRE AW"):
                        record_data["GRE AW"] = text.replace("GRE AW", "").strip()

            date_tag = main_row.select_one("td:nth-child(3)")
            try:
                result_id = int(link_tag['href'].split("/result/")[1].split("#")[0])
                date_added = date_tag.get_text(strip=True) if date_tag else None
                entry = {"id": result_id, "date_added": date_added}
                entry.update(record_data)
                entries.append(entry)
            except Exception:
                pass

            i += 2
        else:
            i += 1

    return entries


def _scrape_page(page_entry: dict):
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
    except Exception:
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
        Each dict corresponds to one survey entry, with keys such as "id",
        "url", "term", and GRE fields.
    """
    all_entries = []
    page_num = 1  # Initial page to start from

    # Keep grabbing entries until the target count is reached
    while len(all_entries) < target_count:
        page_range = range(page_num, page_num + batch_size)
        print(f"Scraping survey pages {page_range[0]}–{page_range[-1]}...")

        with ThreadPoolExecutor(max_workers=100) as executor:
            results = list(executor.map(_scrape_survey_page, page_range))

        batch_entries = [e for sublist in results for e in sublist]

        # Filter out entries that are already loaded
        if max_id:
            batch_entries = [e for e in batch_entries if e["id"] > max_id]

        # If no new entries found, stop early
        if not batch_entries:
            print("No new entries found in this batch. Stopping early.")
            break

        all_entries.extend(batch_entries)
        page_num += batch_size

    all_entries = all_entries[:target_count]
    print(f"Collected {len(all_entries)} survey entries. Fetching details...")

    # Fetch detailed entry pages
    with ThreadPoolExecutor(max_workers=300) as executor:
        detailed = list(executor.map(_scrape_page, all_entries))

    return [d for d in detailed if d]
