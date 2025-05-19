
# ===== job_folder.py =====

# file: data/job_folder.py
import os

def get_job_dir(customer, label_size, job_ticket, po, date_str):
    base_path = r"Z:\3 Encoding and Printing Files\Customers Encoding Files"
    cust_dir  = os.path.join(base_path, customer)
    size_dir  = os.path.join(cust_dir,   label_size)
    job_name  = f"{date_str} - {po} - {job_ticket}"
    return os.path.join(size_dir, job_name)


