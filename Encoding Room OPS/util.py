import os, re
import csv
import datetime
from config import SERIALS_CSV_PATH, SETTINGS_JSON, DEFAULT_SETTINGS
import json
import ast


CUSTOMERS_ROOT = r"Z:\3 Encoding and Printing Files\Customers Encoding Files"
LABEL_SIZE_ROOT = r"Z:\3 Encoding and Printing Files\Encoding Ops\label_sizes.txt"

def get_all_customers():
    return [d for d in os.listdir(CUSTOMERS_ROOT) if os.path.isdir(os.path.join(CUSTOMERS_ROOT, d))]


def _load_label_sizes(path: str = LABEL_SIZE_ROOT) -> list[str]:
    """
    Read label-size definitions from *path*.

    * If the file starts with '[' we assume it’s a literal Python list and
      parse it with ast.literal_eval().
    * Otherwise we treat it as “one label per line”.
    """
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read().strip()

    # Case 1 – literal Python list
    if raw.startswith("[") and raw.endswith("]"):
        try:
            data = ast.literal_eval(raw)
            if isinstance(data, list):
                return [str(item).strip() for item in data if str(item).strip()]
        except (SyntaxError, ValueError):
            pass  # fallback to next case

    # Case 2 – one label per line (ALWAYS return here if not list)
    return [line.strip() for line in raw.splitlines() if line.strip()]
        
        
def get_all_label_sizes():
    """
    Returns a sorted, deduplicated list of label sizes from file.
    """
    import os
    sizes = set()
    if os.path.isfile(LABEL_SIZE_ROOT):
        with open(LABEL_SIZE_ROOT, "r", encoding="utf-8") as f:
            data = f.read()
            for entry in data.split(","):
                val = entry.strip()
                # basic validation: must look like "int x int" or "float x float"
                import re
                if re.match(r"^\d+(\.\d+)?\s*x\s*\d+(\.\d+)?$", val):
                    sizes.add(re.sub(r"\s+", " ", val))  # normalize spaces
    return sorted(sizes)



def get_inlay_types():
    # Reads from 'popular_inlays.txt' in PROJECT ROOT
    with open(r"Z:\3 Encoding and Printing Files\Encoding Ops\label_types.txt") as f:
        return [line.strip() for line in f if line.strip()]



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