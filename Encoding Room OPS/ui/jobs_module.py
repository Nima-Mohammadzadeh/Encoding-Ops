# === File: ui/jobs_module.py ===
from PyQt6.QtWidgets import (
    QWidget, QSplitter, QListWidget, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout, QMessageBox, QDialog, QFormLayout,
    QComboBox, QLineEdit, QSpinBox, QTabWidget, QCompleter
)
from PyQt6.QtCore import QThread, QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QIntValidator

import os
import datetime

from data.jobdata import JobData
from workflow.encoding_checklist import EncodingChecklistTab
from database_tab import DatabaseTab
from workflow.database_generator import DatabaseGeneratorTab
from workflow.roll_tracker import RollTrackerStep
from workflow.bartender_step import BarTenderStep
from workflow.test_print import TestPrintStep
from workflow.docs_export import DocsExportStep
from ui.module_selector import ModuleSelectionDialog
from data.job_db import get_shift_db_path, ShiftJobDB, get_latest_db_path
from data.job_folder import get_job_dir
from util import get_all_customers, get_all_label_sizes, get_inlay_types

CUSTOMERS_ROOT = r"Z:\3 Encoding and Printing Files\Customers Encoding Files"


class JobFolderWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, job_dir):
        super().__init__()
        self.job_dir = job_dir

    def run(self):
        try:
            for subdir in ("Print", "Data", "Roll Tracker", "Reports", "Checklist"):
                os.makedirs(os.path.join(self.job_dir, subdir), exist_ok=True)
            self.finished.emit(self.job_dir)
        except Exception as e:
            self.error.emit(str(e))


class JobsModuleWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Database setup
        latest_db = get_latest_db_path()
        if latest_db:
            self.job_db = ShiftJobDB(latest_db)
        else:
            shift_path = get_shift_db_path()
            self.job_db = ShiftJobDB(shift_path[0]) if shift_path else None

        # UI setup
        split = QSplitter()
        # Left panel: job list and New Job button
        self.job_list = QListWidget()
        self.new_btn = QPushButton("New Job")
        self.new_btn.setMaximumWidth(150)
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("All Jobs"))
        left_layout.addWidget(self.job_list)
        left_layout.addWidget(self.new_btn)
        left_panel = QWidget()
        left_panel.setLayout(left_layout)

        # Right panel: placeholder or workflow
        self.right_panel = QWidget()
        self.right_panel_layout = QVBoxLayout()
        self.right_panel_layout.addWidget(QLabel("No job selected."))
        self.right_panel.setLayout(self.right_panel_layout)

        split.addWidget(left_panel)
        split.addWidget(self.right_panel)
        split.setStretchFactor(1, 2)

        main_layout = QHBoxLayout()
        main_layout.addWidget(split)
        self.setLayout(main_layout)

        # State
        self.jobs = []

        # Signals
        self.job_list.currentRowChanged.connect(self.select_job)
        self.new_btn.clicked.connect(self.new_job_dialog)

    def select_job(self, row):
        # Clear right panel
        while self.right_panel_layout.count():
            item = self.right_panel_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        # Show selected job
        if 0 <= row < len(self.jobs):
            widget = SingleJobWorkflowWidget(self.jobs[row], self)
            self.right_panel_layout.addWidget(widget)
        else:
            self.right_panel_layout.addWidget(QLabel("No job selected."))

    def new_job_dialog(self, prefill=None):
        dlg = JobWizard(prefill, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if not data:
                return
            # Prepare job directory path
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            job_dir = get_job_dir(
                data['customer'], data['label_size'],
                data['job_ticket'], data['customer_po'], date_str
            )
            # Create folders asynchronously
            self.create_job_folders_async(job_dir, lambda path: self.finish_job_creation(data, path))

    def create_job_folders_async(self, job_dir, callback):
        self.folder_thread = QThread()
        self.folder_worker = JobFolderWorker(job_dir)
        self.folder_worker.moveToThread(self.folder_thread)
        self.folder_thread.started.connect(self.folder_worker.run)
        self.folder_worker.finished.connect(lambda path: callback(path))
        self.folder_worker.finished.connect(self.folder_thread.quit)
        self.folder_worker.finished.connect(self.folder_worker.deleteLater)
        self.folder_worker.error.connect(self.on_folder_error)
        self.folder_thread.finished.connect(self.folder_thread.deleteLater)
        self.folder_thread.start()

    def finish_job_creation(self, data, folder_path):
        job_name = f"{data['customer']} - {data['job_ticket']} - {data['label_size']}"
        job = JobData(job_name, data['job_ticket'], data['qty'])
        job.checklist_data = data
        job.folder_path = folder_path
        # Save to database
        job_id = self.job_db.add_job(job)
        self.jobs.append(job)
        self.job_list.addItem(job_name)
        QMessageBox.information(
            self, "Folder Created",
            f"Job folder created at:\n{folder_path}\nJob added."
        )
        # DEFER selection to the event loop so the UI isn't blocked by widget construction
        QTimer.singleShot(0, lambda: self.job_list.setCurrentRow(len(self.jobs) - 1))
        

    def on_folder_error(self, err_msg):
        QMessageBox.critical(
            self, "Job Folder Error",
            f"Failed to create folders:\n{err_msg}"
        )


class JobWizard(QDialog):
    def __init__(self, data: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Job")
        form = QFormLayout(self)

        custs = get_all_customers()
        self.customer = QComboBox()
        self.customer.setEditable(True)
        self.customer.addItems(custs)
        self.customer.setCompleter(QCompleter(custs, self))
        form.addRow("Customer", self.customer)

        self.jobticket = QLineEdit(); form.addRow("Job Ticket", self.jobticket)
        self.partnum = QLineEdit(); form.addRow("Part Num", self.partnum)
        self.po = QLineEdit(); form.addRow("Customer PO", self.po)
        self.item = QLineEdit(); form.addRow("Item", self.item)

        inlays = get_inlay_types()
        self.inlay_type = QComboBox()
        self.inlay_type.setEditable(True)
        self.inlay_type.addItems(inlays)
        self.inlay_type.setCompleter(QCompleter(inlays, self))
        form.addRow("Inlay Type", self.inlay_type)

        all_label_sizes = get_all_label_sizes()
        self.label_size = QComboBox()
        self.label_size.setEditable(True)
        self.label_size.addItems(all_label_sizes)
        self.label_size.setCompleter(QCompleter(all_label_sizes, self))
        form.addRow("Label Size", self.label_size)

        self.qty = QLineEdit()
        self.qty.setValidator(QIntValidator(1,99999999)); form.addRow("QTY", self.qty)

        self.overage = QSpinBox()
        self.overage.setSuffix("%"); self.overage.setRange(0,100)
        form.addRow("Overage %", self.overage)

        self.upc = QLineEdit()
        self.upc.setMaxLength(15)
        self.upc.textChanged.connect(self._format_upc)
        form.addRow("UPC", self.upc)

        self.labels_per_roll = QLineEdit()
        self.labels_per_roll.setValidator(QIntValidator(1,99999999))
        self.labels_per_roll.textChanged.connect(self._calc_rolls)
        form.addRow("Labels Per Roll", self.labels_per_roll)

        self.rolls = QLabel("0")
        form.addRow("Rolls", self.rolls)

        btns = QHBoxLayout()
        done = QPushButton("Finish"); cancel = QPushButton("Cancel")
        btns.addWidget(done); btns.addWidget(cancel)
        form.addRow(btns)
        done.clicked.connect(self._finish)
        cancel.clicked.connect(self.reject)
        self.setLayout(form)

        self._result = None
        if data: self.fill(data)

    def _format_upc(self, txt):
        digits = "".join(c for c in txt if c.isdigit())[:12]
        pretty = ""
        for i, d in enumerate(digits):
            pretty += d
            if i in (2,5,8):
                pretty += " "
        self.upc.blockSignals(True)
        self.upc.setText(pretty)
        self.upc.blockSignals(False)

    def _calc_rolls(self):
        try:
            qty = int(self.qty.text())
            per = int(self.labels_per_roll.text())
            rolls = (qty + per - 1) // per
            self.rolls.setText(str(rolls))
        except:
            self.rolls.setText("0")

    def _finish(self):
        self.result = {
            "customer": self.customer.currentText(),
            "job_ticket": self.jobticket.text(),
            "part_num": self.partnum.text(),
            "customer_po": self.po.text(),
            "item": self.item.text(),
            "inlay_type": self.inlay_type.currentText(),
            "label_size": self.label_size.currentText(),
            "qty": int(self.qty.text().replace(",", "")),
            "overage": str(self.overage.value()),
            "upc": "".join(c for c in self.upc.text() if c.isdigit())[:12],
            "labels_per_roll": int(self.labels_per_roll.text().replace(",", "")),
            "rolls": int(self.rolls.text()),
        }
        self.accept()

    def get_data(self):
        return getattr(self, 'result', None)


class SingleJobWorkflowWidget(QWidget):
    def __init__(self, job: JobData, jobs_modwidget=None):
        super().__init__()
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tabs.addTab(EncodingChecklistTab(job, jobs_modwidget), "Checklist")
        self.tabs.addTab(DatabaseTab(job), "Database")
        self.tabs.addTab(RollTrackerStep(job), "Roll Tracker")
        self.tabs.addTab(BarTenderStep(job), "BarTender")
        self.tabs.addTab(TestPrintStep(job), "Test Print & QC")
        self.tabs.addTab(DocsExportStep(job), "Docs/Export")
        layout.addWidget(self.tabs)
        self.setLayout(layout)
