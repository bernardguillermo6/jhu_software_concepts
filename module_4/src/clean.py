#!/usr/bin/env python3

import re
import json
import subprocess
from bs4 import BeautifulSoup


def _parse_decision_date(notification_str):
    """Extract a date in DD/MM/YYYY format from a notification string.

    Input:
        notification_str (str | None): A string containing notification details,
            possibly with a date in DD/MM/YYYY format. Can be None or empty.

    Output:
        str | None: The extracted date string in DD/MM/YYYY format if found,
        otherwise None.
    """
    if not notification_str:
        return None
    match = re.search(r"\d{2}/\d{2}/\d{4}", notification_str)
    return match.group(0) if match else None


def clean_data(raw_entries, target_count):
    """Clean and normalize raw admissions data into structured records.

    Input:
        raw_entries (list[dict]): A list of raw scraped admission entries, where
            each entry has a "data" field containing HTML snippets keyed by labels.
        target_count (int): Maximum number of cleaned records to return. If more
            entries exist, the list will be trimmed.

    Output:
        list[dict]: A list of cleaned records, each containing standardized fields
        (program, university, comments, status, GPA, GRE, etc.), along with
        acceptance/rejection dates parsed from notifications.
    """
    cleaned = []  # initial list to hold records

    # setting the fields to be in each record, regardless if they exist
    FIELD_MAP = {
        "program": ["Program"],
        "university": ["Institution"],
        "comments": ["Notes"],
        "date_added": ["Date Added"],
        "applicant_status": ["Decision", "Status"],
        "acceptance_date": ["Notification"],
        "rejection_date": ["Notification"],
        "term": ["Term"],
        "US/International": ["Degree's Country of Origin"],
        "GRE Score": ["GRE Score"],
        "GRE V Score": ["GRE V Score"],
        "Degree": ["Degree Type"],
        "GPA": ["Undergrad GPA"],
        "GRE AW": ["GRE AW"],
    }

    # loop through all the admissions data
    for entry in raw_entries:
        pairs = entry["data"]

        record = {}  # initialize dictionary to hold pairs
        for field, labels in FIELD_MAP.items():
            value = None
            for label in labels:
                raw_html = pairs.get(label)
                if raw_html and raw_html.strip():
                    soup = BeautifulSoup(raw_html, "html.parser")

                    # try to find label span
                    span_label = soup.find("span", string=lambda t: t and t.strip() == label)
                    if span_label and span_label.next_sibling:
                        # use the sibling text as the value if found
                        value = span_label.next_sibling.get_text(strip=True)
                        break
                    # fallback: just get text of the html
                    value = soup.get_text(strip=True)
                    if value:
                        break
            record[field] = value

        # combine program and university into a single "program" field for LLM
        program_val = record.get("program") or ""
        university_val = record.get("university") or ""
        combined = f"{program_val}, {university_val}".strip().rstrip(",")
        record["program"] = combined

        record["URL"] = entry.get("url")  # add the URL

        # return application status so we can set the acceptance or rejection date
        decision = record.get("applicant_status")
        notification = pairs.get("Notification")

        if decision == "Accepted":
            record["acceptance_date"] = _parse_decision_date(notification)
            record["rejection_date"] = None
        elif decision == "Rejected":
            record["rejection_date"] = _parse_decision_date(notification)
            record["acceptance_date"] = None
        else:
            record["rejection_date"] = None
            record["acceptance_date"] = None

        cleaned.append(record)  # adding cleaned record

    # trim the list if we got too many records
    if len(cleaned) > target_count:
        cleaned = cleaned[:target_count]

    return cleaned


def clean_with_llm(input_file: str, output_file: str):
    """Run an LLM process on an input jsonl file and return the cleaned results.

    This function calls an external LLM script (`module_2/llm_hosting/app.py`)
    to process entries from a jsonl file, writes the cleaned output to another
    jsonl file, and then reads the results back into Python objects.

    Input:
        input_file (str): Path to the input jsonl file containing raw entries.
        output_file (str): Path where the cleaned jsonl output will be saved.

    Output:
        list[dict]: A list of dictionaries representing the cleaned entries
        as parsed from the output jsonl file.

    Raises:
        RuntimeError: If the LLM subprocess fails and returns a non-zero exit code.
    """
    print(f"Cleaning entries with LLM. Input: {input_file}, Output: {output_file}")
    # Command to call the LLM from module_2 and output results
    cmd = [
        "python",
        "src/llm_hosting/app.py",
        "--file", input_file,
        "--out", output_file,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"LLM failed: {result.stderr}")

    print(f"Finished cleaning with LLM. Output saved to: {output_file}")

    # Read JSONL back into Python objects
    with open(output_file) as f:
        cleaned_data = [json.loads(line) for line in f]

    return cleaned_data

