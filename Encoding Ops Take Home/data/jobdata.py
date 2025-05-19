# ===== jobdata.py =====


# file: data/jobdata.py

import datetime


class JobData:
    def __init__(self, name, code, qty, modules=None):   # <--- add the modules param & default
        self.db_id = None
        self.name = name
        self.code = code
        self.qty = qty
        self.start_time = datetime.datetime.now()
        self.serials = []
        self.bartender_file = ""
        self.rolls = []
        self.status = "Initialized"
        self.checklist_data = {
            'customer': '',
            'job_ticket': '',
            'part_num': '',
            'customer_po': '',
            'item': '',
            'inlay_type': '',
            'label_size': '',
            'qty': '',
            'overage': '',
            'upc': '',
            'start': '',
            'stop': '',
            'labels_per_roll': '',
            'rolls': ''
        }
        # Store module selections (add this new attribute)
        self.modules = modules or {
            "show_checklist": True,
            "show_dbgen": True,
            "show_rolltracker": True
        }
