# serial_tracker.py

import csv, os, datetime

SERIAL_TRACKER_CSV = r"Z:\3 Encoding and Printing Files\Operations\serial_tracker.csv"

def get_next_available_serial():
    if not os.path.exists(SERIAL_TRACKER_CSV):
        return 1
    with open(SERIAL_TRACKER_CSV, newline='', encoding='utf-8') as f:
        rdr = list(csv.DictReader(f))
        if not rdr:
            return 1
        return int(rdr[-1]['next_serial'])

def reserve_serials(job_ticket, customer, label_size, qty):
    start = get_next_available_serial()
    stop = start + qty - 1
    next_serial = stop + 1
    row = {
        "date": datetime.datetime.now().strftime('%Y-%m-%d'),
        "job_ticket": job_ticket,
        "customer": customer,
        "label_size": label_size,
        "serial_start": start,
        "serial_stop": stop,
        "next_serial": next_serial
    }
    file_exists = os.path.exists(SERIAL_TRACKER_CSV)
    with open(SERIAL_TRACKER_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    return (start, stop)