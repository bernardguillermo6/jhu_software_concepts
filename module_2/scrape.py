#!/usr/bin/env python3

import urllib3
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

http = urllib3.PoolManager()


def _scrape_survey_page(page_num: int):
    # scrape the main survey page (https://www.thegradcafe.com/survey)

    url = f"https://www.thegradcafe.com/survey/?page={page_num}" # setting the url for the survey pages

    try:
        response = http.request("GET", url, timeout=10.0)
        if response.status != 200:
            return []
    except Exception:
        return []

    soup = BeautifulSoup(response.data, "html.parser")
    entries = []

    # grabbing the tr tags
    rows = soup.select("tr")

    # setting the regex search pattern for the term
    import re
    term_pattern = re.compile(r"^(Fall|Spring|Summer|Winter|F|S|Su|W)\s*\d{2,4}$", re.IGNORECASE)

    i = 0
    # records can span 2-3 tr tags, depending on if there's comments
    while i < len(rows):
        row = rows[i]

        # setting the result url tag, which always shows up in the first tr
        link_tag = row.select_one("a[href^='/result/']")
        if link_tag:
            main_row = row
            badges_row = rows[i + 1] if i + 1 < len(rows) else None

            record_data = {}

            # if it's the second tr, search for the badges
            if badges_row:
                for div in badges_row.find_all("div", class_="tw-inline-flex"):
                    text = div.get_text(strip=True)
                    # set the term if found
                    if term_pattern.match(text):
                        record_data["term"] = text
                    # set the GRE score if found
                    elif text.startswith("GRE ") and not text.startswith("GRE V") and not text.startswith("GRE AW"):
                        record_data["GRE Score"] = text.replace("GRE", "").strip()
                    # set the GRE Verbal score if found
                    elif text.startswith("GRE V"):
                        record_data["GRE V Score"] = text.replace("GRE V", "").strip()
                    # set the GRE Analytical Writing if found
                    elif text.startswith("GRE AW"):
                        record_data["GRE AW"] = text.replace("GRE AW", "").strip()

            # set the date added
            date_tag = main_row.select_one("td:nth-child(3)")
            try:
                result_id = int(link_tag['href'].split("/result/")[1].split("#")[0])
                date_added = date_tag.get_text(strip=True) if date_tag else None

                # combine all the records to a dictionary
                entry = {
                    "id": result_id,
                    "date_added": date_added,
                }
                entry.update(record_data)
                entries.append(entry)
            except Exception:
                pass

            i += 2 # move past the main row and badges row
        else:
            i += 1 # skip rows that are not the start of a record

    return entries


def _scrape_page(page_entry: dict):
    # scrape the results page (https://www.thegradcafe.com/result/) to get additional details
    # grabbing details from the results page as it's easier to parse than the survey page

    page_id = page_entry["id"]

    url = f"https://www.thegradcafe.com/result/{page_id}" # set the url for the results page

    try:
        # load the results page, return nothing if fails
        response = http.request("GET", url, timeout=10.0)
        if response.status != 200:
            return None

        soup = BeautifulSoup(response.data, "html.parser")
        pairs = {} # initialize dictionary to store data

        # loop through each <div> inside <dl> to extract dt/dd pairs
        for block in soup.select("dl > div"):
            dt = block.find("dt") 
            dd = block.find("dd") 
            if dt and dd:
                key = dt.get_text(strip=True)  # clean the labels
                value = dd.get_text(strip=True) # clean the values
                pairs[key] = value # adding pairs to the dictionary

        # combining values from survey and results page
        pairs["Date Added"] = page_entry["date_added"]
        pairs["Term"] = page_entry.get("term")  
        pairs["GRE Score"] = page_entry.get("GRE Score")
        pairs["GRE V Score"] = page_entry.get("GRE V Score")
        pairs["GRE AW"] = page_entry.get("GRE AW")
  
        # return combined data
        return {"id": page_id, "url": url, "data": pairs}
    except Exception:
        return None


def scrape_data(target_count, batch_size):
    # scrape the pages from https://www.thegradcafe.com until we get the target number of entries

    all_entries = [] 
    page_num = 1 

    # continue scraping results until we get to the target count
    while len(all_entries) < target_count:

        # determine the page range for the surveys based on batch size
        page_range = list(range(page_num, page_num + batch_size))
        print(f"Scraping survey pages {page_range[0]}–{page_range[-1]}...")

        # using threading to concurrently scrape survey pages
        with ThreadPoolExecutor(max_workers=100) as executor:
            results = list(executor.map(_scrape_survey_page, page_range))        

        # flatten the results and remove empty entries
        batch_entries = [entry for sublist in results for entry in sublist]
        if not batch_entries:
            break  
        all_entries.extend(batch_entries)

        print(f"Collected {len(all_entries)} survey entries so far...")
        page_num += batch_size # initialize the next batch of pages

    all_entries = all_entries[:target_count]
    print(f"Collected {len(all_entries)} survey entries. Fetching details...")

    # use threading to concurrently run results pages 
    with ThreadPoolExecutor(max_workers=300) as executor:
        detailed = list(executor.map(_scrape_page, all_entries))

    # return entries
    return [d for d in detailed if d]
