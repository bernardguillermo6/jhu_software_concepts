#!/usr/bin/env python3

import json
from scrape import scrape_data
from clean import clean_data


def save_data(data, filename="applicant_data.json"):
    # save to a JSON file

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def load_data(filename="applicant_data.json"):
    # load data from a JSON file
    with open(filename, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    print("Starting scrape...")
    raw = scrape_data(target_count=55000, batch_size=500) 
    print("Cleaning data...")
    cleaned = clean_data(raw, target_count=50000) 
    print(f"Saving {len(cleaned)} cleaned entries...")
    save_data(cleaned)
    print("Done")