from PyQt6.QtWidgets import (
    QWidget, QSplitter, QListWidget, QPushButton, QLabel,
    QHBoxLayout, QVBoxLayout, QMessageBox, QDialog, QFormLayout,
    QComboBox, QLineEdit, QSpinBox, QTabWidget, QCompleter,
    QListWidgetItem
)
from PyQt6.QtCore import QThread, QObject, pyqtSignal, QTimer, Qt
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
from ui.job_list_item_widget import JobListItemWidget
from data.job_db import JobDB, get_db_path
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

        # Database
        db_path = get_db_path()
        self.job_db = JobDB(db_path)

        # Caches for right panel widgets per job
        self.active_job_tabs = {}
        self.completed_job_tabs = {}

        # --- UI ---
        split = QSplitter()

        # --- LEFT PANEL: TabWidget with lists ---
        self.job_list_active = QListWidget()
        self.job_list_completed = QListWidget()
        self.job_tab_widget = QTabWidget()
        self.job_tab_widget.addTab(self.job_list_active, "Active Jobs")
        self.job_tab_widget.addTab(self.job_list_completed, "Completed")

        self.new_btn = QPushButton("New Job")
        self.new_btn.setMaximumWidth(150)
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.job_tab_widget)
        left_layout.addWidget(self.new_btn)
        left_panel = QWidget()
        left_panel.setLayout(left_layout)
        # --- END LEFT

        # --- RIGHT PANEL ---
        self.right_panel = QWidget()
        self.right_panel_layout = QVBoxLayout()
        self.right_panel_layout.addWidget(QLabel("No job selected."))
        self.right_panel.setLayout(self.right_panel_layout)
        # --- END RIGHT

        split.addWidget(left_panel)
        split.addWidget(self.right_panel)
        split.setStretchFactor(1, 2)

        main_layout = QHBoxLayout()
        main_layout.addWidget(split)
        self.setLayout(main_layout)

        # State
        self.jobs = []

        # Load jobs initially
        self.load_jobs_from_db()

        # Signals
        self.job_list_active.currentRowChanged.connect(self.select_active_job)
        self.job_list_completed.currentRowChanged.connect(self.select_completed_job)
        self.new_btn.clicked.connect(self.new_job_dialog)

    def load_jobs_from_db(self):
        # Load all jobs from DB
        self.jobs.clear()
        self.job_list_active.clear()
        self.job_list_completed.clear()

        if not self.job_db:
            return

        jobs_raw = self.job_db.list_jobs()
        self.jobs = []

        # Build and append JobData objects to self.jobs list
        for jd in jobs_raw:
            job = JobData(jd['job_name'], jd['job_ticket'], jd['qty'])
            job.db_id = jd['id']
            job.status = jd['status']
            job.folder_path = jd['folder_path']
            job.checklist_data = jd.get('checklist_data', {})
            self.jobs.append(job)

        # Add to widget lists with proper item widget and controls
        for job in [j for j in self.jobs if j.status != 'completed']:
            item = QListWidgetItem()
            widget = JobListItemWidget(
                job.name,
                remove_callback=lambda checked=False, j=job: self.remove_job(j),
                complete_callback=lambda checked=False, j=job: self.complete_job(j),
                is_completed=False
            )
            item.setSizeHint(widget.sizeHint())
            self.job_list_active.addItem(item)
            self.job_list_active.setItemWidget(item, widget)

        for job in [j for j in self.jobs if j.status == 'completed']:
            item = QListWidgetItem()
            widget = JobListItemWidget(
                job.name + " (COMPLETED)",
                remove_callback=None,
                complete_callback=None,
                is_completed=True
            )
            item.setSizeHint(widget.sizeHint())
            self.job_list_completed.addItem(item)
            self.job_list_completed.setItemWidget(item, widget)

    # ----------- Job Selection -----------

    def select_active_job(self, row):
        self._select_job(row, active=True)

    def select_completed_job(self, row):
        self._select_job(row, active=False)

    def _select_job(self, row, active=True):
        # Remove old right panel widget(s)
        while self.right_panel_layout.count():
            item = self.right_panel_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
        # Choose correct filtered list
        jobs = [ job for job in self.jobs if job.status != 'completed' ] if active else [ job for job in self.jobs if job.status == 'completed']
        if 0 <= row < len(jobs):
            job = jobs[row]
            tab_cache = self.active_job_tabs if job.status != 'completed' else self.completed_job_tabs
            if job.db_id in tab_cache:
                widget = tab_cache[job.db_id]
            else:
                widget = SingleJobWorkflowWidget(job, self)
                tab_cache[job.db_id] = widget
            self.right_panel_layout.addWidget(widget)
        else:
            self.right_panel_layout.addWidget(QLabel("No job selected."))

    # ----------- New/Remove/Complete -----------

    def new_job_dialog(self, prefill=None):
        dlg = JobWizard(prefill, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if not data:
                return
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            job_dir = get_job_dir(
                data['customer'], data['label_size'],
                data['job_ticket'], data['customer_po'], date_str
            )
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
        job.status = 'active'
        job_id = self.job_db.add_job(job)
        job.db_id = job_id
        self.jobs.append(job)
        self.load_jobs_from_db()
        QMessageBox.information(
            self, "Folder Created",
            f"Job folder created at:\n{folder_path}\nJob added."
        )
        # Auto-select the new job (last in active)
        QTimer.singleShot(0, lambda: self.job_list_active.setCurrentRow(self.job_list_active.count() - 1))

    def on_folder_error(self, err_msg):
        QMessageBox.critical(
            self, "Job Folder Error",
            f"Failed to create folders:\n{err_msg}"
        )

    def remove_job(self, job):
        if hasattr(job, 'db_id'):
            if QMessageBox.question(self, "Remove Job", f"Remove job '{job.name}' from database?") == QMessageBox.StandardButton.Yes:
                self.job_db.delete_job(job.db_id)
                self.active_job_tabs.pop(job.db_id, None)
                self.completed_job_tabs.pop(job.db_id, None)
                self.load_jobs_from_db()

    def complete_job(self, job):
        if hasattr(job, 'db_id'):
            if QMessageBox.question(self, "Complete Job", f"Mark job '{job.name}' as completed? This will move the job to the Completed tab.") == QMessageBox.StandardButton.Yes:
                self.job_db.mark_job_completed(job.db_id)
                self.active_job_tabs.pop(job.db_id, None)
                self.completed_job_tabs.pop(job.db_id, None)
                self.load_jobs_from_db()

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