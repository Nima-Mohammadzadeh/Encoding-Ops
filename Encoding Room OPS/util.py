import os
import csv
import datetime
from config import SERIALS_CSV_PATH, SETTINGS_JSON, DEFAULT_SETTINGS
import json
import re

CUSTOMERS_ROOT = r"Z:\3 Encoding and Printing Files\Customers Encoding Files"

def get_all_customers():
    # List all customer folders under CUSTOMERS_ROOT
    return [
        name for name in os.listdir(CUSTOMERS_ROOT)
        if os.path.isdir(os.path.join(CUSTOMERS_ROOT, name))
    ]

def get_all_label_sizes():
    # Finds all folders in customers/*/ that look like number x number (any spaces, repeats removed)
    label_size_pattern = re.compile(r'^\s*(\d+)\s*x\s*(\d+)\s*$', re.IGNORECASE)
    results = set()
    for customer in get_all_customers():
        customer_dir = os.path.join(CUSTOMERS_ROOT, customer)
        if not os.path.isdir(customer_dir):
            continue
        for name in os.listdir(customer_dir):
            if os.path.isdir(os.path.join(customer_dir, name)):
                match = label_size_pattern.match(name)
                if match:
                    # Normalize spaces to "num x num" form
                    results.add(f"{match.group(1)} x {match.group(2)}")
    return sorted(results)



def current_time_str():
    return datetime.datetime.now().strftime("%H:%M:%S")

def load_settings():
    if not os.path.exists(SETTINGS_JSON):
        with open(SETTINGS_JSON, "w") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=2)
        return DEFAULT_SETTINGS.copy()
    with open(SETTINGS_JSON, "r") as f:
        return json.load(f)

def save_settings(data):
    with open(SETTINGS_JSON, "w") as f:
        json.dump(data, f, indent=2)

def get_latest_serial():
    try:
        with open(SERIALS_CSV_PATH, "r", newline="") as f:
            reader = csv.reader(f)
            next(reader, None)
            row = next(reader, None)
            return int(row[0]) if row and row[0].isdigit() else 1
    except Exception:
        os.makedirs(os.path.dirname(SERIALS_CSV_PATH), exist_ok=True)
        with open(SERIALS_CSV_PATH, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(['latest_serial'])
            writer.writerow(['1'])
        return 1

def update_latest_serial(new_serial):
    with open(SERIALS_CSV_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["latest_serial"])
        writer.writerow([str(new_serial)])