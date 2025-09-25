"""
Data cleaning utilities for admissions survey entries.

This module normalizes scraped HTML data into structured dictionaries,
parses decision dates, and provides an interface to run external LLM-based
cleaning. It includes:

- `_parse_decision_date`: Extracts DD/MM/YYYY dates from notifications.
- `clean_data`: Cleans raw HTML fields into standardized Python records.
- `clean_with_llm`: Invokes an external LLM script to perform advanced
  data cleaning and save results to disk.
"""

#!/usr/bin/env python3

import json
import re
import subprocess

from bs4 import BeautifulSoup


# Mapping of output fields to possible raw labels
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


def _parse_decision_date(notification_str):
    """
    Extract a date in DD/MM/YYYY format from a notification string.

    Parameters
    ----------
    notification_str : str or None
        A string containing notification details, possibly with a date in
        ``DD/MM/YYYY`` format. Can be None or empty.

    Returns
    -------
    str or None
        The extracted date string in ``DD/MM/YYYY`` format if found,
        otherwise ``None``.
    """
    if not notification_str:
        return None
    match = re.search(r"\d{2}/\d{2}/\d{4}", notification_str)
    return match.group(0) if match else None


def _extract_label_text(raw_html: str, label: str) -> str | None:
    """Extract the text content after a specific label span in raw HTML."""
    soup = BeautifulSoup(raw_html, "html.parser")
    span_label = soup.find("span", string=lambda t: t and t.strip() == label)
    if span_label and span_label.next_sibling:
        return span_label.next_sibling.get_text(strip=True)
    return soup.get_text(strip=True) if soup.get_text(strip=True) else None


def _build_record(pairs: dict) -> dict:
    """Extract raw fields into a normalized record dictionary."""
    record = {}
    for field, labels in FIELD_MAP.items():
        value = None
        for label in labels:
            raw_html = pairs.get(label)
            if raw_html and raw_html.strip():
                value = _extract_label_text(raw_html, label)
                if value:
                    break
        record[field] = value
    return record


def _combine_program_and_university(record: dict) -> str:
    """Return combined program and university string."""
    program_val = record.get("program") or ""
    university_val = record.get("university") or ""
    combined = f"{program_val}, {university_val}".strip().rstrip(",")
    return combined


def _apply_decision_logic(record: dict, pairs: dict) -> None:
    """Mutate record with acceptance/rejection dates based on decision."""
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


def clean_data(raw_entries, target_count):
    """
    Clean and normalize raw admissions data into structured records.

    Parameters
    ----------
    raw_entries : list of dict
        A list of raw scraped admission entries. Each entry has a ``data`` field
        containing HTML snippets keyed by labels.
    target_count : int
        Maximum number of cleaned records to return. If more entries exist,
        the list will be trimmed.

    Returns
    -------
    list of dict
        A list of cleaned records, each containing standardized fields
        (program, university, comments, status, GPA, GRE, etc.), along with
        acceptance/rejection dates parsed from notifications.
    """
    cleaned = []

    for entry in raw_entries:
        pairs = entry["data"]
        record = _build_record(pairs)
        record["program"] = _combine_program_and_university(record)
        record["URL"] = entry.get("url")
        _apply_decision_logic(record, pairs)
        cleaned.append(record)

    return cleaned[:target_count]


def clean_with_llm(input_file: str, output_file: str):
    """
    Run an LLM process on an input JSONL file and return the cleaned results.

    This function calls an external LLM script (`src/llm_hosting/app.py`)
    to process entries from a JSONL file, writes the cleaned output to another
    JSONL file, and then reads the results back into Python objects.

    Parameters
    ----------
    input_file : str
        Path to the input JSONL file containing raw entries.
    output_file : str
        Path where the cleaned JSONL output will be saved.

    Returns
    -------
    list of dict
        A list of dictionaries representing the cleaned entries as parsed
        from the output JSONL file.

    Raises
    ------
    RuntimeError
        If the LLM subprocess fails and returns a non-zero exit code.
    """
    print(f"Cleaning entries with LLM. Input: {input_file}, Output: {output_file}")
    cmd = [
        "python",
        "src/llm_hosting/app.py",
        "--file",
        input_file,
        "--out",
        output_file,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        raise RuntimeError(f"LLM failed: {result.stderr}")

    print(f"Finished cleaning with LLM. Output saved to: {output_file}")

    with open(output_file, encoding="utf-8") as f:
        cleaned_data = [json.loads(line) for line in f]

    return cleaned_data


def parse_decision_date_for_test(s: str):
    """Public wrapper to test the private _parse_decision_date."""
    return _parse_decision_date(s)
