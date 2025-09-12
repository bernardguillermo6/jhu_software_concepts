#!/usr/bin/env python3

import json


def save_data(data, filename="applicant_data.json"):
    # save to a JSON file

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def load_data(filename="applicant_data.json"):
    # load data from a JSON file
    with open(filename, "r") as f:
        return json.load(f)


def load_jsonl(filename="applicant_data.jsonl"):
    with open(filename, "r") as f:
        return [json.loads(line) for line in f if line.strip()]
