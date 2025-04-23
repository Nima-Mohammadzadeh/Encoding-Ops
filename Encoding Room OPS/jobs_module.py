# jobs_module.py
from PyQt6.QtWidgets import *
from jobdata import JobData
from encoding_checklist import EncodingChecklistTab
from database_tab import DatabaseTab   # new file/class below!
from roll_tracker import RollTrackerStep
from bartender_step import BarTenderStep
from test_print import TestPrintStep
from docs_export import DocsExportStep
from PyQt6.QtGui import QIntValidator
import os
import datetime

# --- Utility functions from above ---
from util import get_all_customers, get_all_label_sizes

CUSTOMERS_ROOT = r"Z:\3 Encoding and Printing Files\Customers Encoding Files"

def get_label_sizes_for_customer(customer):
    cust_dir = os.path.join(CUSTOMERS_ROOT, customer)
    if not os.path.exists(cust_dir):
        return []
    import re
    label_size_pattern = re.compile(r'^\s*(\d+)\s*x\s*(\d+)\s*$', re.IGNORECASE)
    label_sizes = []
    for name in os.listdir(cust_dir):
        if os.path.isdir(os.path.join(cust_dir, name)):
            match = label_size_pattern.match(name)
            if match:
                label_sizes.append(f"{match.group(1)} x {match.group(2)}")
    return sorted(set(label_sizes))

def make_job_folder(customer, label_size, job_ticket, po):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    folder_name = f"{today} - {po} - {job_ticket}"
    path = os.path.join(CUSTOMERS_ROOT, customer, label_size, folder_name)
    os.makedirs(os.path.join(path, "Print"), exist_ok=True)
    os.makedirs(os.path.join(path, "Data"), exist_ok=True)
    os.makedirs(os.path.join(path, "Roll Tracker"), exist_ok=True)
    os.makedirs(os.path.join(path, "Reports"), exist_ok=True)
    os.makedirs(os.path.join(path, "Checklist"), exist_ok=True)
    return path

class JobWizard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Job")
        layout = QFormLayout(self)

        # Customer Dropdown with autocomplete+typing
        self.customer_box = QComboBox()
        self.customer_box.setEditable(True)
        customers = get_all_customers()
        self.customer_box.addItems(customers)
        self.customer_box.setCompleter(QCompleter(customers, self))
        self.customer_box.currentIndexChanged.connect(self.update_label_sizes)

        layout.addRow("Customer:", self.customer_box)

        # Label Size Dropdown with autocomplete+typing
        self.label_size_box = QComboBox()
        self.label_size_box.setEditable(True)
        # Initially: all sizes across all customers (not per-customer, per your request)
        all_label_sizes = get_all_label_sizes()
        self.label_size_box.addItems(all_label_sizes)
        self.label_size_box.setCompleter(QCompleter(all_label_sizes, self))

        layout.addRow("Label Size:", self.label_size_box)

        # Job Ticket #
        self.jobticket_box = QLineEdit()
        layout.addRow("Job Ticket #:", self.jobticket_box)

        # PO Number
        self.po_box = QLineEdit()
        layout.addRow("PO Number:", self.po_box)

        # Printer Quantity
        self.qty_box = QLineEdit()
        self.qty_box.setValidator(QIntValidator(1, 99999999))
        layout.addRow("Label QTY:", self.qty_box)

        # Finish/cancel
        btns = QHBoxLayout()
        self.ok_btn = QPushButton("Finish")
        self.cancel_btn = QPushButton("Cancel")
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        layout.addRow(btns)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self._result_data = None

    def update_label_sizes(self):
        # Optionally, you could make this update based on selected customer,
        # or ignore (leave at all sizes) if you want to allow all.
        pass  # in this version label sizes are all from all customers

    def accept(self):
        # Validate
        cust = self.customer_box.currentText().strip()
        lblsz = self.label_size_box.currentText().strip()
        jobticket = self.jobticket_box.text().strip()
        po = self.po_box.text().strip()
        qty = self.qty_box.text().strip()
        if not (cust and lblsz and jobticket and qty and qty.isdigit()):
            QMessageBox.warning(self, "Error", "Please fill all fields (QTY must be number).")
            return
        self._result_data = {
            "customer": cust,
            "label_size": lblsz,
            "job_ticket": jobticket,
            "po": po,
            "qty": int(qty),
        }
        super().accept()

    def get_data(self):
        return self._result_data

class SingleJobWorkflowWidget(QWidget):
    def __init__(self, job: JobData):
        super().__init__()
        layout = QVBoxLayout()
        tabs = QTabWidget()
        tabs.addTab(EncodingChecklistTab(job), "Checklist")
        tabs.addTab(DatabaseTab(job), "Database")
        tabs.addTab(RollTrackerStep(job), "Roll Tracker")
        tabs.addTab(BarTenderStep(job), "BarTender")
        tabs.addTab(TestPrintStep(job), "Test Print & QC")
        tabs.addTab(DocsExportStep(job), "Docs/Export")
        layout.addWidget(tabs)
        self.setLayout(layout)

class JobsModuleWidget(QWidget):
    def __init__(self):
        super().__init__()
        split = QSplitter()
        self.job_list = QListWidget()
        self.new_btn = QPushButton("New Job")
        self.new_btn.setMaximumWidth(150)
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("All Jobs"))
        left_layout.addWidget(self.job_list)
        left_layout.addWidget(self.new_btn)
        left_panel = QWidget()
        left_panel.setLayout(left_layout)
        self.right_panel = QWidget()
        self.right_panel_layout = QVBoxLayout()
        self.right_panel_layout.addWidget(QLabel("No job selected."))
        self.right_panel.setLayout(self.right_panel_layout)
        split.addWidget(left_panel)
        split.addWidget(self.right_panel)
        split.setStretchFactor(1, 2)
        layout = QHBoxLayout()
        layout.addWidget(split)
        self.setLayout(layout)
        self.jobs = []
        self.job_list.currentRowChanged.connect(self.select_job)
        self.new_btn.clicked.connect(self.new_job_dialog)

    def select_job(self, row):
        if row >= 0 and row < len(self.jobs):
            job = self.jobs[row]
            while self.right_panel_layout.count():
                item = self.right_panel_layout.takeAt(0)
                widget = item.widget()
                if widget: widget.deleteLater()
            self.right_panel_layout.addWidget(SingleJobWorkflowWidget(job))
        else:
            while self.right_panel_layout.count():
                item = self.right_panel_layout.takeAt(0)
                widget = item.widget()
                if widget: widget.deleteLater()
            self.right_panel_layout.addWidget(QLabel("No job selected."))

    def new_job_dialog(self):
        dlg = JobWizard(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if not data:
                return
            folder_path = make_job_folder(
                data['customer'], data['label_size'], data['job_ticket'], data['po']
            )
            job_name = f"{data['customer']} - {data['job_ticket']} - {data['label_size']}"
            job = JobData(job_name, data['job_ticket'], data['qty'])
            job.folder_path = folder_path
            # Autofill checklist
            job.checklist_data['customer'] = data['customer']
            job.checklist_data['job_ticket'] = data['job_ticket']
            job.checklist_data['qty'] = data['qty']
            job.checklist_data['label_size'] = data['label_size']
            job.checklist_data['customer_po'] = data['po']
            self.jobs.append(job)
            self.job_list.addItem(job_name)
            self.job_list.setCurrentRow(len(self.jobs) - 1)
            QMessageBox.information(self, "Folder Created",
                f"Job folder created at:\n{folder_path}\nJob added.")