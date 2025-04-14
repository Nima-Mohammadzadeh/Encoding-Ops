import sys, os, csv, math, sqlite3, threading
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QListWidget, QListWidgetItem, QDialog, QFormLayout, QDialogButtonBox,
    QMessageBox, QProgressBar, QSpinBox, QScrollArea, QStackedWidget, QTabWidget, QComboBox,
    QAction, QFileDialog, QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject

# Import Watchdog modules
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Global dropdown lists
LABEL_TYPES = ["261-M730", "241-M730", "300-M730", "430-M730", "300-M730-CW"]
PRINTER_OPTIONS = ["P1", "P2", "P3", "P4", "P5", "P7", "P8", "P12", "P13", "P15"]
TEAM_MEMBERS = ["Nima", "Deepak", "Ram", "Somya", "Brett"]

# =============================================================================
# Database Manager
# =============================================================================
class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT,
                job_ticket TEXT,
                label_type TEXT,
                quantity INTEGER,
                labels_per_roll INTEGER,
                printer_name TEXT,
                created_at TEXT,
                completed INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roll_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                roll_number INTEGER,
                action TEXT,
                note TEXT,
                timestamp TEXT,
                FOREIGN KEY(job_id) REFERENCES jobs(id)
            )
        ''')
        self.connection.commit()

    def add_job(self, customer, job_ticket, label_type, quantity, labels_per_roll, printer_name):
        cursor = self.connection.cursor()
        created_at = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO jobs (customer, job_ticket, label_type, quantity, labels_per_roll, printer_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (customer, job_ticket, label_type, quantity, labels_per_roll, printer_name, created_at))
        self.connection.commit()
        return cursor.lastrowid

    def get_active_jobs(self):
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT id, customer, job_ticket, label_type, quantity, labels_per_roll, printer_name, created_at 
            FROM jobs WHERE completed=0
        ''')
        return cursor.fetchall()

    def get_completed_jobs(self):
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT id, customer, job_ticket, label_type, quantity, labels_per_roll, printer_name, created_at 
            FROM jobs WHERE completed=1
        ''')
        return cursor.fetchall()

    def log_roll_action(self, job_id, roll_number, action, note=""):
        cursor = self.connection.cursor()
        timestamp = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO roll_tracking (job_id, roll_number, action, note, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (job_id, roll_number, action, note, timestamp))
        self.connection.commit()

    def update_job_completion(self, job_id, completed=1):
        cursor = self.connection.cursor()
        cursor.execute('UPDATE jobs SET completed=? WHERE id=?', (completed, job_id))
        self.connection.commit()

    def update_job(self, job_id, customer, job_ticket, label_type, quantity, labels_per_roll, printer_name):
        cursor = self.connection.cursor()
        cursor.execute('''
            UPDATE jobs
            SET customer=?, job_ticket=?, label_type=?, quantity=?, labels_per_roll=?, printer_name=?
            WHERE id=?
        ''', (customer, job_ticket, label_type, quantity, labels_per_roll, printer_name, job_id))
        self.connection.commit()

    def get_roll_tracking(self, job_id):
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT roll_number, action, note, timestamp FROM roll_tracking WHERE job_id=? ORDER BY timestamp
        ''', (job_id,))
        return cursor.fetchall()

# =============================================================================
# CSV Event Handler & Monitor
# =============================================================================
class CSVEventHandler(FileSystemEventHandler):
    def __init__(self, monitor):
        self.monitor = monitor

    def on_modified(self, event):
        if not event.is_directory and event.src_path.lower().endswith('.csv'):
            self.monitor.process_csv(event.src_path)

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith('.csv'):
            self.monitor.file_row_counts[event.src_path] = 0
            self.monitor.process_csv(event.src_path)

class WatchdogCSVMonitor(QObject):
    update_signal = pyqtSignal(dict)  # {printer_name: {"pass": cumulative_pass, "fail": cumulative_fail}}

    def __init__(self, directory):
        super().__init__()
        self.directory = directory
        self.file_row_counts = {}
        self.cumulative_counts = {}
        self.observer = Observer()
        self.event_handler = CSVEventHandler(self)

    def start(self):
        self.observer.schedule(self.event_handler, self.directory, recursive=False)
        threading.Thread(target=self.observer.start, daemon=True).start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

    def process_csv(self, csv_path):
        new_counts = {}
        if csv_path not in self.file_row_counts:
            self.file_row_counts[csv_path] = 0
        try:
            with open(csv_path, "r", newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                total_rows = len(rows)
                last_count = self.file_row_counts[csv_path]
                new_rows = rows[last_count:]
                for row in new_rows:
                    failure_msg = row.get("Failure Message", "").strip()
                    printer = row.get("Printer Name", "Printer_1").strip()
                    if printer not in new_counts:
                        new_counts[printer] = {"pass": 0, "fail": 0}
                    if failure_msg == "Pass (Label)":
                        new_counts[printer]["pass"] += 1
                    elif failure_msg == "Fail (Label)":
                        new_counts[printer]["fail"] += 1
                self.file_row_counts[csv_path] = total_rows
        except Exception as e:
            print("Error processing CSV:", e)
            return
        for printer, counts in new_counts.items():
            if printer not in self.cumulative_counts:
                self.cumulative_counts[printer] = {"pass": 0, "fail": 0}
            self.cumulative_counts[printer]["pass"] += counts["pass"]
            self.cumulative_counts[printer]["fail"] += counts["fail"]
        if new_counts:
            self.update_signal.emit(self.cumulative_counts)

# =============================================================================
# RollWidget: Represents a roll with flexible stages and team dropdown.
# =============================================================================
class RollWidget(QWidget):
    def __init__(self, job_id, roll_number, labels_goal, printer_name, db_manager):
        super().__init__()
        self.job_id = job_id
        self.roll_number = roll_number
        self.labels_goal = labels_goal
        self.printer_name = printer_name
        self.db_manager = db_manager

        self.current_progress = 0
        # States: idle, running, paused, finished
        self.state = "idle"
        self.baseline_pass = None
        self.baseline_fail = None

        self.notes_history = []  # List of note strings

        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout()

        # Controls layout (first row)
        self.controls_layout = QHBoxLayout()
        self.label = QLabel(f"Roll {self.roll_number}")
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(self.labels_goal)
        self.progress_bar.setValue(self.current_progress)
        self.pass_count_label = QLabel("Pass: 0")
        self.fail_count_label = QLabel("Fail: 0")
        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        # Team dropdown with default placeholder "Select User"
        self.team_dropdown = QComboBox()
        self.team_dropdown.addItem("Select User")
        for member in TEAM_MEMBERS:
            self.team_dropdown.addItem(member)
        self.finish_btn = QPushButton("Finish")
        self.start_btn.clicked.connect(self.start_roll)
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.finish_btn.clicked.connect(self.finish_roll)
        for widget in [self.label, self.progress_bar, self.pass_count_label, self.fail_count_label,
                       self.start_btn, self.pause_btn, self.team_dropdown, self.finish_btn]:
            self.controls_layout.addWidget(widget)
        self.main_layout.addLayout(self.controls_layout)

        # Dynamic Notes Section (initially hidden)
        self.notes_section = QWidget()
        self.notes_section_layout = QVBoxLayout()
        self.note_input = QTextEdit()
        self.note_input.setFixedHeight(50)
        self.notes_buttons_layout = QHBoxLayout()
        self.submit_note_btn = QPushButton("Submit Note")
        self.discard_note_btn = QPushButton("Discard Note")
        self.notes_buttons_layout.addWidget(self.submit_note_btn)
        self.notes_buttons_layout.addWidget(self.discard_note_btn)
        self.submit_note_btn.clicked.connect(self.submit_note)
        self.discard_note_btn.clicked.connect(self.discard_note)
        self.notes_history_label = QLabel("Notes History:")
        self.notes_history_container = QWidget()
        self.notes_history_layout = QVBoxLayout()
        self.notes_history_container.setLayout(self.notes_history_layout)
        self.notes_section_layout.addWidget(self.note_input)
        self.notes_section_layout.addLayout(self.notes_buttons_layout)
        self.notes_section_layout.addWidget(self.notes_history_label)
        self.notes_section_layout.addWidget(self.notes_history_container)
        self.notes_section.setLayout(self.notes_section_layout)
        self.notes_section.setVisible(False)
        self.main_layout.addWidget(self.notes_section)

        self.setLayout(self.main_layout)

    def start_roll(self):
        if self.state != "running":
            self.state = "running"
            self.baseline_pass = None
            self.baseline_fail = None
            self.start_btn.setEnabled(False)
            self.pause_btn.setText("Pause")
            self.db_manager.log_roll_action(self.job_id, self.roll_number, "start")
            print(f"Roll {self.roll_number} started for Job {self.job_id}")

    def toggle_pause(self):
        if self.state == "running":
            self.state = "paused"
            self.pause_btn.setText("Unpause")
            self.notes_section.setVisible(True)
            print(f"Roll {self.roll_number} paused for Job {self.job_id} at {self.current_progress} labels")
        elif self.state == "paused":
            self.state = "running"
            self.pause_btn.setText("Pause")
            self.notes_section.setVisible(False)
            self.db_manager.log_roll_action(self.job_id, self.roll_number, "resume")
            print(f"Roll {self.roll_number} resumed for Job {self.job_id}")

    def submit_note(self):
        note_text = self.note_input.toPlainText().strip()
        if note_text:
            team_name = self.team_dropdown.currentText()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            full_note = f"[{timestamp}] {team_name} - Paused at {self.current_progress}: {note_text}"
            self.notes_history.append(full_note)
            note_label = QLabel(full_note)
            self.notes_history_layout.addWidget(note_label)
            self.db_manager.log_roll_action(self.job_id, self.roll_number, "pause note", full_note)
            self.note_input.clear()

    def discard_note(self):
        self.note_input.clear()
        self.notes_section.setVisible(False)

    def finish_roll(self):
        if self.state in ["running", "paused"]:
            team_name = self.team_dropdown.currentText()
            if team_name == "Select User":
                QMessageBox.warning(self, "Missing Team Selection", "Please select a team member before finishing the roll.")
                return
            finish_note = f"Finished by {team_name} at {self.current_progress} labels."
            self.db_manager.log_roll_action(self.job_id, self.roll_number, "finish", finish_note)
            print(f"Roll {self.roll_number} finished for Job {self.job_id} by {team_name}")
            self.state = "finished"
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.finish_btn.setEnabled(False)
            self.team_dropdown.setEnabled(False)
            self.notes_section.setVisible(False)

    def update_progress(self, cumulative_data):
        if self.state != "running":
            return
        if self.baseline_pass is None:
            self.baseline_pass = cumulative_data.get("pass", 0)
            self.baseline_fail = cumulative_data.get("fail", 0)
            return
        delta_pass = cumulative_data.get("pass", 0) - self.baseline_pass
        delta_fail = cumulative_data.get("fail", 0) - self.baseline_fail
        self.current_progress = min(delta_pass, self.labels_goal)
        self.progress_bar.setValue(self.current_progress)
        self.pass_count_label.setText(f"Pass: {delta_pass}")
        self.fail_count_label.setText(f"Fail: {delta_fail}")

# =============================================================================
# ReportViewDialog: Displays a detailed, hierarchical report for a completed job.
# =============================================================================
class ReportViewDialog(QDialog):
    def __init__(self, job, db_manager, parent=None):
        super().__init__(parent)
        self.job = job
        self.db_manager = db_manager
        self.setWindowTitle("Detailed Job Report")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        # Display job details
        job_details = QLabel(f"Job Report for {self.job[2]} - {self.job[1]}\n"
                             f"Label Type: {self.job[3]}, Quantity: {self.job[4]}, "
                             f"Labels per Roll: {self.job[5]}, Printer: {self.job[6]}, "
                             f"Created: {self.job[7]}")
        layout.addWidget(job_details)
        # Create hierarchical report using QTreeWidget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Roll", "Action", "Note", "Timestamp"])
        layout.addWidget(self.tree)
        # Populate tree with roll tracking data grouped by roll number
        tracking = self.db_manager.get_roll_tracking(self.job[0])
        rolls = {}
        for roll, action, note, timestamp in tracking:
            rolls.setdefault(roll, []).append((action, note, timestamp))
        for roll in sorted(rolls.keys()):
            roll_item = QTreeWidgetItem([str(roll)])
            for action, note, timestamp in rolls[roll]:
                child = QTreeWidgetItem(["", action, note, timestamp])
                roll_item.addChild(child)
            self.tree.addTopLevelItem(roll_item)
        # Download button for report
        download_btn = QPushButton("Download Report")
        download_btn.clicked.connect(self.download_report)
        layout.addWidget(download_btn)
        self.setLayout(layout)

    def download_report(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Report", "", "Text Files (*.txt)")
        if path:
            with open(path, "w") as f:
                f.write(f"Job Report for {self.job[2]} - {self.job[1]}\n")
                f.write(f"Label Type: {self.job[3]}, Quantity: {self.job[4]}, Labels per Roll: {self.job[5]}, Printer: {self.job[6]}, Created: {self.job[7]}\n\n")
                for i in range(self.tree.topLevelItemCount()):
                    roll_item = self.tree.topLevelItem(i)
                    f.write(f"Roll {roll_item.text(0)}:\n")
                    for j in range(roll_item.childCount()):
                        child = roll_item.child(j)
                        f.write(f"  Action: {child.text(1)}, Note: {child.text(2)}, Timestamp: {child.text(3)}\n")
                    f.write("\n")
            QMessageBox.information(self, "Report Saved", f"Report saved to {path}")

# =============================================================================
# DatabaseViewerDialog: Allows exploration and deletion of database entries.
# =============================================================================
class DatabaseViewerDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Database Viewer")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        self.jobs_table = QTableWidget()
        self.rolls_table = QTableWidget()
        self.tab_widget.addTab(self.jobs_table, "Jobs")
        self.tab_widget.addTab(self.rolls_table, "Roll Tracking")
        layout.addWidget(self.tab_widget)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(refresh_btn)
        self.setLayout(layout)
        self.load_data()

    def load_data(self):
        # Load jobs table using column names (index 1)
        jobs = self.db_manager.connection.execute("SELECT * FROM jobs").fetchall()
        header = [desc[1] for desc in self.db_manager.connection.execute("PRAGMA table_info(jobs)").fetchall()]
        self.jobs_table.setColumnCount(len(header))
        self.jobs_table.setRowCount(len(jobs))
        self.jobs_table.setHorizontalHeaderLabels(header)
        for i, row in enumerate(jobs):
            for j, value in enumerate(row):
                self.jobs_table.setItem(i, j, QTableWidgetItem(str(value)))
        # Load roll tracking table using column names (index 1)
        rolls = self.db_manager.connection.execute("SELECT * FROM roll_tracking").fetchall()
        header2 = [desc[1] for desc in self.db_manager.connection.execute("PRAGMA table_info(roll_tracking)").fetchall()]
        self.rolls_table.setColumnCount(len(header2))
        self.rolls_table.setRowCount(len(rolls))
        self.rolls_table.setHorizontalHeaderLabels(header2)
        for i, row in enumerate(rolls):
            for j, value in enumerate(row):
                self.rolls_table.setItem(i, j, QTableWidgetItem(str(value)))

    def delete_selected_job(self):
        selected = self.jobs_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Delete Job", "Please select a job to delete.")
            return
        row = selected[0].row()
        job_id = int(self.jobs_table.item(row, 0).text())
        reply = QMessageBox.question(self, "Confirm Delete", "Delete selected job?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_manager.connection.execute("DELETE FROM jobs WHERE id=?", (job_id,))
            self.db_manager.connection.commit()
            self.load_data()

    def delete_selected_roll(self):
        selected = self.rolls_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Delete Roll", "Please select a roll entry to delete.")
            return
        row = selected[0].row()
        roll_id = int(self.rolls_table.item(row, 0).text())
        reply = QMessageBox.question(self, "Confirm Delete", "Delete selected roll entry?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_manager.connection.execute("DELETE FROM roll_tracking WHERE id=?", (roll_id,))
            self.db_manager.connection.commit()
            self.load_data()

# =============================================================================
# EditJobDialog: Allows editing an active job.
# =============================================================================
class EditJobDialog(QDialog):
    def __init__(self, job, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.job = job
        self.job_data = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Edit Job")
        layout = QFormLayout(self)
        self.customer_input = QLineEdit(self.job[1])
        self.job_ticket_input = QLineEdit(self.job[2])
        self.label_type_dropdown = QComboBox()
        self.label_type_dropdown.addItems(LABEL_TYPES)
        idx = self.label_type_dropdown.findText(self.job[3])
        if idx >= 0:
            self.label_type_dropdown.setCurrentIndex(idx)
        self.quantity_input = QSpinBox()
        self.quantity_input.setMaximum(100000)
        self.quantity_input.setValue(self.job[4])
        self.labels_per_roll_input = QSpinBox()
        self.labels_per_roll_input.setMaximum(10000)
        self.labels_per_roll_input.setValue(self.job[5])
        self.printer_dropdown = QComboBox()
        self.printer_dropdown.addItems(PRINTER_OPTIONS)
        idx = self.printer_dropdown.findText(self.job[6])
        if idx >= 0:
            self.printer_dropdown.setCurrentIndex(idx)
        layout.addRow("Customer:", self.customer_input)
        layout.addRow("Job Ticket #:", self.job_ticket_input)
        layout.addRow("Label Type:", self.label_type_dropdown)
        layout.addRow("Quantity:", self.quantity_input)
        layout.addRow("Labels Per Roll:", self.labels_per_roll_input)
        layout.addRow("Printer:", self.printer_dropdown)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        self.job_data = {
            "customer": self.customer_input.text(),
            "job_ticket": self.job_ticket_input.text(),
            "label_type": self.label_type_dropdown.currentText(),
            "quantity": self.quantity_input.value(),
            "labels_per_roll": self.labels_per_roll_input.value(),
            "printer_name": self.printer_dropdown.currentText()
        }
        super().accept()

# =============================================================================
# CompletedJobsWidget: Lists completed jobs in a summarized report view.
# =============================================================================
class CompletedJobsWidget(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Completed Jobs"))
        self.jobs_list = QListWidget()
        self.jobs_list.itemClicked.connect(self.show_job_details)
        layout.addWidget(self.jobs_list)
        self.detail_area = QStackedWidget()
        self.detail_area.addWidget(QLabel("Select a completed job to view details."))
        layout.addWidget(self.detail_area)
        self.setLayout(layout)
        self.load_completed_jobs()

    def load_completed_jobs(self):
        self.jobs_list.clear()
        jobs = self.db_manager.get_completed_jobs()
        for job in jobs:
            item_text = f"{job[2]} - {job[1]} (Printer: {job[6]})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, job)
            self.jobs_list.addItem(item)

    def show_job_details(self, item):
        job = item.data(Qt.UserRole)
        job_detail = JobDetailWidget(job, self.db_manager)
        self.detail_area.addWidget(job_detail)
        self.detail_area.setCurrentWidget(job_detail)

# =============================================================================
# JobFormDialog: A dialog to add a new job (with dropdowns).
# =============================================================================
class JobFormDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.job_data = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Add New Job")
        layout = QFormLayout(self)
        self.customer_input = QLineEdit()
        self.job_ticket_input = QLineEdit()
        self.label_type_dropdown = QComboBox()
        self.label_type_dropdown.addItems(LABEL_TYPES)
        self.quantity_input = QSpinBox()
        self.quantity_input.setMaximum(100000)
        self.labels_per_roll_input = QSpinBox()
        self.labels_per_roll_input.setMaximum(10000)
        self.printer_dropdown = QComboBox()
        self.printer_dropdown.addItems(PRINTER_OPTIONS)
        layout.addRow("Customer:", self.customer_input)
        layout.addRow("Job Ticket #:", self.job_ticket_input)
        layout.addRow("Label Type:", self.label_type_dropdown)
        layout.addRow("Quantity:", self.quantity_input)
        layout.addRow("Labels Per Roll:", self.labels_per_roll_input)
        layout.addRow("Printer:", self.printer_dropdown)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        if not self.customer_input.text() or not self.job_ticket_input.text():
            QMessageBox.warning(self, "Input Error", "Customer and Job Ticket # are required.")
            return
        self.job_data = {
            "customer": self.customer_input.text(),
            "job_ticket": self.job_ticket_input.text(),
            "label_type": self.label_type_dropdown.currentText(),
            "quantity": self.quantity_input.value(),
            "labels_per_roll": self.labels_per_roll_input.value(),
            "printer_name": self.printer_dropdown.currentText()
        }
        super().accept()

# =============================================================================
# ReportViewDialog: Displays a detailed, hierarchical report for a completed job.
# =============================================================================
class ReportViewDialog(QDialog):
    def __init__(self, job, db_manager, parent=None):
        super().__init__(parent)
        self.job = job
        self.db_manager = db_manager
        self.setWindowTitle("Detailed Job Report")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        # Job details header
        job_details = QLabel(f"Job Report for {self.job[2]} - {self.job[1]}\n"
                             f"Label Type: {self.job[3]}, Quantity: {self.job[4]}, "
                             f"Labels per Roll: {self.job[5]}, Printer: {self.job[6]}, "
                             f"Created: {self.job[7]}")
        layout.addWidget(job_details)
        # Hierarchical report using QTreeWidget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Roll", "Action", "Note", "Timestamp"])
        layout.addWidget(self.tree)
        # Populate tree with roll tracking data grouped by roll number
        tracking = self.db_manager.get_roll_tracking(self.job[0])
        rolls = {}
        for roll, action, note, timestamp in tracking:
            rolls.setdefault(roll, []).append((action, note, timestamp))
        for roll in sorted(rolls.keys()):
            roll_item = QTreeWidgetItem([str(roll)])
            for action, note, timestamp in rolls[roll]:
                child = QTreeWidgetItem(["", action, note, timestamp])
                roll_item.addChild(child)
            self.tree.addTopLevelItem(roll_item)
        # Download button for report
        download_btn = QPushButton("Download Report")
        download_btn.clicked.connect(self.download_report)
        layout.addWidget(download_btn)
        self.setLayout(layout)

    def download_report(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Report", "", "Text Files (*.txt)")
        if path:
            with open(path, "w") as f:
                f.write(f"Job Report for {self.job[2]} - {self.job[1]}\n")
                f.write(f"Label Type: {self.job[3]}, Quantity: {self.job[4]}, Labels per Roll: {self.job[5]}, Printer: {self.job[6]}, Created: {self.job[7]}\n\n")
                for i in range(self.tree.topLevelItemCount()):
                    roll_item = self.tree.topLevelItem(i)
                    f.write(f"Roll {roll_item.text(0)}:\n")
                    for j in range(roll_item.childCount()):
                        child = roll_item.child(j)
                        f.write(f"  Action: {child.text(1)}, Note: {child.text(2)}, Timestamp: {child.text(3)}\n")
                    f.write("\n")
            QMessageBox.information(self, "Report Saved", f"Report saved to {path}")

# =============================================================================
# DatabaseViewerDialog: Allows exploration and deletion of database entries.
# =============================================================================
class DatabaseViewerDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Database Viewer")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        self.jobs_table = QTableWidget()
        self.rolls_table = QTableWidget()
        self.tab_widget.addTab(self.jobs_table, "Jobs")
        self.tab_widget.addTab(self.rolls_table, "Roll Tracking")
        layout.addWidget(self.tab_widget)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(refresh_btn)
        self.setLayout(layout)
        self.load_data()

    def load_data(self):
        # Load jobs table using column names (index 1)
        jobs = self.db_manager.connection.execute("SELECT * FROM jobs").fetchall()
        header = [desc[1] for desc in self.db_manager.connection.execute("PRAGMA table_info(jobs)").fetchall()]
        self.jobs_table.setColumnCount(len(header))
        self.jobs_table.setRowCount(len(jobs))
        self.jobs_table.setHorizontalHeaderLabels(header)
        for i, row in enumerate(jobs):
            for j, value in enumerate(row):
                self.jobs_table.setItem(i, j, QTableWidgetItem(str(value)))
        # Load roll tracking table using column names (index 1)
        rolls = self.db_manager.connection.execute("SELECT * FROM roll_tracking").fetchall()
        header2 = [desc[1] for desc in self.db_manager.connection.execute("PRAGMA table_info(roll_tracking)").fetchall()]
        self.rolls_table.setColumnCount(len(header2))
        self.rolls_table.setRowCount(len(rolls))
        self.rolls_table.setHorizontalHeaderLabels(header2)
        for i, row in enumerate(rolls):
            for j, value in enumerate(row):
                self.rolls_table.setItem(i, j, QTableWidgetItem(str(value)))

    def delete_selected_job(self):
        selected = self.jobs_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Delete Job", "Please select a job to delete.")
            return
        row = selected[0].row()
        job_id = int(self.jobs_table.item(row, 0).text())
        reply = QMessageBox.question(self, "Confirm Delete", "Delete selected job?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_manager.connection.execute("DELETE FROM jobs WHERE id=?", (job_id,))
            self.db_manager.connection.commit()
            self.load_data()

    def delete_selected_roll(self):
        selected = self.rolls_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Delete Roll", "Please select a roll entry to delete.")
            return
        row = selected[0].row()
        roll_id = int(self.rolls_table.item(row, 0).text())
        reply = QMessageBox.question(self, "Confirm Delete", "Delete selected roll entry?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_manager.connection.execute("DELETE FROM roll_tracking WHERE id=?", (roll_id,))
            self.db_manager.connection.commit()
            self.load_data()

# =============================================================================
# EditJobDialog: Allows editing an active job.
# =============================================================================
class EditJobDialog(QDialog):
    def __init__(self, job, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.job = job
        self.job_data = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Edit Job")
        layout = QFormLayout(self)
        self.customer_input = QLineEdit(self.job[1])
        self.job_ticket_input = QLineEdit(self.job[2])
        self.label_type_dropdown = QComboBox()
        self.label_type_dropdown.addItems(LABEL_TYPES)
        idx = self.label_type_dropdown.findText(self.job[3])
        if idx >= 0:
            self.label_type_dropdown.setCurrentIndex(idx)
        self.quantity_input = QSpinBox()
        self.quantity_input.setMaximum(100000)
        self.quantity_input.setValue(self.job[4])
        self.labels_per_roll_input = QSpinBox()
        self.labels_per_roll_input.setMaximum(10000)
        self.labels_per_roll_input.setValue(self.job[5])
        self.printer_dropdown = QComboBox()
        self.printer_dropdown.addItems(PRINTER_OPTIONS)
        idx = self.printer_dropdown.findText(self.job[6])
        if idx >= 0:
            self.printer_dropdown.setCurrentIndex(idx)
        layout.addRow("Customer:", self.customer_input)
        layout.addRow("Job Ticket #:", self.job_ticket_input)
        layout.addRow("Label Type:", self.label_type_dropdown)
        layout.addRow("Quantity:", self.quantity_input)
        layout.addRow("Labels Per Roll:", self.labels_per_roll_input)
        layout.addRow("Printer:", self.printer_dropdown)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        self.job_data = {
            "customer": self.customer_input.text(),
            "job_ticket": self.job_ticket_input.text(),
            "label_type": self.label_type_dropdown.currentText(),
            "quantity": self.quantity_input.value(),
            "labels_per_roll": self.labels_per_roll_input.value(),
            "printer_name": self.printer_dropdown.currentText()
        }
        super().accept()

# =============================================================================
# CompletedJobsWidget: Lists completed jobs in a summarized report view.
# =============================================================================
class CompletedJobsWidget(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Completed Jobs"))
        self.jobs_list = QListWidget()
        self.jobs_list.itemClicked.connect(self.show_job_details)
        layout.addWidget(self.jobs_list)
        self.detail_area = QStackedWidget()
        self.detail_area.addWidget(QLabel("Select a completed job to view details."))
        layout.addWidget(self.detail_area)
        self.setLayout(layout)
        self.load_completed_jobs()

    def load_completed_jobs(self):
        self.jobs_list.clear()
        jobs = self.db_manager.get_completed_jobs()
        for job in jobs:
            item_text = f"{job[2]} - {job[1]} (Printer: {job[6]})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, job)
            self.jobs_list.addItem(item)

    def show_job_details(self, item):
        job = item.data(Qt.UserRole)
        job_detail = JobDetailWidget(job, self.db_manager)
        self.detail_area.addWidget(job_detail)
        self.detail_area.setCurrentWidget(job_detail)

# =============================================================================
# JobFormDialog: A dialog to add a new job (with dropdowns).
# =============================================================================
class JobFormDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.job_data = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Add New Job")
        layout = QFormLayout(self)
        self.customer_input = QLineEdit()
        self.job_ticket_input = QLineEdit()
        self.label_type_dropdown = QComboBox()
        self.label_type_dropdown.addItems(LABEL_TYPES)
        self.quantity_input = QSpinBox()
        self.quantity_input.setMaximum(100000)
        self.labels_per_roll_input = QSpinBox()
        self.labels_per_roll_input.setMaximum(10000)
        self.printer_dropdown = QComboBox()
        self.printer_dropdown.addItems(PRINTER_OPTIONS)
        layout.addRow("Customer:", self.customer_input)
        layout.addRow("Job Ticket #:", self.job_ticket_input)
        layout.addRow("Label Type:", self.label_type_dropdown)
        layout.addRow("Quantity:", self.quantity_input)
        layout.addRow("Labels Per Roll:", self.labels_per_roll_input)
        layout.addRow("Printer:", self.printer_dropdown)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        if not self.customer_input.text() or not self.job_ticket_input.text():
            QMessageBox.warning(self, "Input Error", "Customer and Job Ticket # are required.")
            return
        self.job_data = {
            "customer": self.customer_input.text(),
            "job_ticket": self.job_ticket_input.text(),
            "label_type": self.label_type_dropdown.currentText(),
            "quantity": self.quantity_input.value(),
            "labels_per_roll": self.labels_per_roll_input.value(),
            "printer_name": self.printer_dropdown.currentText()
        }
        super().accept()

# =============================================================================
# ReportViewDialog: Displays a detailed, hierarchical report for a completed job.
# =============================================================================
class ReportViewDialog(QDialog):
    def __init__(self, job, db_manager, parent=None):
        super().__init__(parent)
        self.job = job
        self.db_manager = db_manager
        self.setWindowTitle("Detailed Job Report")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        # Job details header
        job_details = QLabel(f"Job Report for {self.job[2]} - {self.job[1]}\n"
                             f"Label Type: {self.job[3]}, Quantity: {self.job[4]}, "
                             f"Labels per Roll: {self.job[5]}, Printer: {self.job[6]}, "
                             f"Created: {self.job[7]}")
        layout.addWidget(job_details)
        # Hierarchical report using QTreeWidget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Roll", "Action", "Note", "Timestamp"])
        layout.addWidget(self.tree)
        # Populate tree with roll tracking data grouped by roll number
        tracking = self.db_manager.get_roll_tracking(self.job[0])
        rolls = {}
        for roll, action, note, timestamp in tracking:
            rolls.setdefault(roll, []).append((action, note, timestamp))
        for roll in sorted(rolls.keys()):
            roll_item = QTreeWidgetItem([str(roll)])
            for action, note, timestamp in rolls[roll]:
                child = QTreeWidgetItem(["", action, note, timestamp])
                roll_item.addChild(child)
            self.tree.addTopLevelItem(roll_item)
        # Download button for report
        download_btn = QPushButton("Download Report")
        download_btn.clicked.connect(self.download_report)
        layout.addWidget(download_btn)
        self.setLayout(layout)

    def download_report(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Report", "", "Text Files (*.txt)")
        if path:
            with open(path, "w") as f:
                f.write(f"Job Report for {self.job[2]} - {self.job[1]}\n")
                f.write(f"Label Type: {self.job[3]}, Quantity: {self.job[4]}, Labels per Roll: {self.job[5]}, Printer: {self.job[6]}, Created: {self.job[7]}\n\n")
                for i in range(self.tree.topLevelItemCount()):
                    roll_item = self.tree.topLevelItem(i)
                    f.write(f"Roll {roll_item.text(0)}:\n")
                    for j in range(roll_item.childCount()):
                        child = roll_item.child(j)
                        f.write(f"  Action: {child.text(1)}, Note: {child.text(2)}, Timestamp: {child.text(3)}\n")
                    f.write("\n")
            QMessageBox.information(self, "Report Saved", f"Report saved to {path}")

# =============================================================================
# DatabaseViewerDialog: Allows exploration and deletion of database entries.
# =============================================================================
class DatabaseViewerDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Database Viewer")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        self.jobs_table = QTableWidget()
        self.rolls_table = QTableWidget()
        self.tab_widget.addTab(self.jobs_table, "Jobs")
        self.tab_widget.addTab(self.rolls_table, "Roll Tracking")
        layout.addWidget(self.tab_widget)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(refresh_btn)
        self.setLayout(layout)
        self.load_data()

    def load_data(self):
        # Load jobs table using column names (index 1)
        jobs = self.db_manager.connection.execute("SELECT * FROM jobs").fetchall()
        header = [desc[1] for desc in self.db_manager.connection.execute("PRAGMA table_info(jobs)").fetchall()]
        self.jobs_table.setColumnCount(len(header))
        self.jobs_table.setRowCount(len(jobs))
        self.jobs_table.setHorizontalHeaderLabels(header)
        for i, row in enumerate(jobs):
            for j, value in enumerate(row):
                self.jobs_table.setItem(i, j, QTableWidgetItem(str(value)))
        # Load roll tracking table using column names (index 1)
        rolls = self.db_manager.connection.execute("SELECT * FROM roll_tracking").fetchall()
        header2 = [desc[1] for desc in self.db_manager.connection.execute("PRAGMA table_info(roll_tracking)").fetchall()]
        self.rolls_table.setColumnCount(len(header2))
        self.rolls_table.setRowCount(len(rolls))
        self.rolls_table.setHorizontalHeaderLabels(header2)
        for i, row in enumerate(rolls):
            for j, value in enumerate(row):
                self.rolls_table.setItem(i, j, QTableWidgetItem(str(value)))

    def delete_selected_job(self):
        selected = self.jobs_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Delete Job", "Please select a job to delete.")
            return
        row = selected[0].row()
        job_id = int(self.jobs_table.item(row, 0).text())
        reply = QMessageBox.question(self, "Confirm Delete", "Delete selected job?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_manager.connection.execute("DELETE FROM jobs WHERE id=?", (job_id,))
            self.db_manager.connection.commit()
            self.load_data()

    def delete_selected_roll(self):
        selected = self.rolls_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Delete Roll", "Please select a roll entry to delete.")
            return
        row = selected[0].row()
        roll_id = int(self.rolls_table.item(row, 0).text())
        reply = QMessageBox.question(self, "Confirm Delete", "Delete selected roll entry?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_manager.connection.execute("DELETE FROM roll_tracking WHERE id=?", (roll_id,))
            self.db_manager.connection.commit()
            self.load_data()

# =============================================================================
# JobDetailWidget: Displays roll tracking; includes "Complete Job" and "View Report" buttons.
# =============================================================================
class JobDetailWidget(QWidget):
    job_completed = pyqtSignal(int)
    def __init__(self, job, db_manager):
        super().__init__()
        self.job = job  # (id, customer, job_ticket, label_type, quantity, labels_per_roll, printer_name, created_at)
        self.db_manager = db_manager
        self.roll_widgets = []
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        details = QLabel(f"Customer: {self.job[1]} | Job Ticket: {self.job[2]} | Label Type: {self.job[3]} | "
                         f"Quantity: {self.job[4]} | Labels/Roll: {self.job[5]} | Printer: {self.job[6]}")
        self.main_layout.addWidget(details)
        total_rolls = math.ceil(self.job[4] / self.job[5])
        self.main_layout.addWidget(QLabel(f"Total Rolls: {total_rolls}"))
        self.roll_container = QVBoxLayout()
        for roll_num in range(1, total_rolls + 1):
            roll_widget = RollWidget(self.job[0], roll_num, self.job[5], self.job[6], self.db_manager)
            self.roll_widgets.append(roll_widget)
            self.roll_container.addWidget(roll_widget)
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.roll_container)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(scroll_area)
        btn_layout = QHBoxLayout()
        self.complete_job_btn = QPushButton("Complete Job")
        self.complete_job_btn.clicked.connect(self.complete_job)
        view_report_btn = QPushButton("View Report")
        view_report_btn.clicked.connect(self.view_report)
        btn_layout.addWidget(self.complete_job_btn)
        btn_layout.addWidget(view_report_btn)
        self.main_layout.addLayout(btn_layout)
        self.setLayout(self.main_layout)

    def update_rolls(self, update_data):
        printer_name = self.job[6]
        if printer_name in update_data:
            cumulative = update_data[printer_name]
            for roll in self.roll_widgets:
                if roll.state == "running":
                    roll.update_progress(cumulative)
                    break

    def complete_job(self):
        reply = QMessageBox.question(self, "Confirm Completion",
                                     "Mark this job as complete?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_manager.update_job_completion(self.job[0], completed=1)
            self.db_manager.log_roll_action(self.job[0], 0, "job completed", "Job marked complete")
            QMessageBox.information(self, "Job Completed", "Job marked as complete.")
            self.complete_job_btn.setEnabled(False)
            self.job_completed.emit(self.job[0])

    def view_report(self):
        report_dialog = ReportViewDialog(self.job, self.db_manager, self)
        report_dialog.exec_()

# =============================================================================
# EditJobDialog: Allows editing an active job.
# =============================================================================
class EditJobDialog(QDialog):
    def __init__(self, job, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.job = job
        self.job_data = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Edit Job")
        layout = QFormLayout(self)
        self.customer_input = QLineEdit(self.job[1])
        self.job_ticket_input = QLineEdit(self.job[2])
        self.label_type_dropdown = QComboBox()
        self.label_type_dropdown.addItems(LABEL_TYPES)
        idx = self.label_type_dropdown.findText(self.job[3])
        if idx >= 0:
            self.label_type_dropdown.setCurrentIndex(idx)
        self.quantity_input = QSpinBox()
        self.quantity_input.setMaximum(100000)
        self.quantity_input.setValue(self.job[4])
        self.labels_per_roll_input = QSpinBox()
        self.labels_per_roll_input.setMaximum(10000)
        self.labels_per_roll_input.setValue(self.job[5])
        self.printer_dropdown = QComboBox()
        self.printer_dropdown.addItems(PRINTER_OPTIONS)
        idx = self.printer_dropdown.findText(self.job[6])
        if idx >= 0:
            self.printer_dropdown.setCurrentIndex(idx)
        layout.addRow("Customer:", self.customer_input)
        layout.addRow("Job Ticket #:", self.job_ticket_input)
        layout.addRow("Label Type:", self.label_type_dropdown)
        layout.addRow("Quantity:", self.quantity_input)
        layout.addRow("Labels Per Roll:", self.labels_per_roll_input)
        layout.addRow("Printer:", self.printer_dropdown)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        self.job_data = {
            "customer": self.customer_input.text(),
            "job_ticket": self.job_ticket_input.text(),
            "label_type": self.label_type_dropdown.currentText(),
            "quantity": self.quantity_input.value(),
            "labels_per_roll": self.labels_per_roll_input.value(),
            "printer_name": self.printer_dropdown.currentText()
        }
        super().accept()

# =============================================================================
# CompletedJobsWidget: Lists completed jobs in a summarized report view.
# =============================================================================
class CompletedJobsWidget(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Completed Jobs"))
        self.jobs_list = QListWidget()
        self.jobs_list.itemClicked.connect(self.show_job_details)
        layout.addWidget(self.jobs_list)
        self.detail_area = QStackedWidget()
        self.detail_area.addWidget(QLabel("Select a completed job to view details."))
        layout.addWidget(self.detail_area)
        self.setLayout(layout)
        self.load_completed_jobs()

    def load_completed_jobs(self):
        self.jobs_list.clear()
        jobs = self.db_manager.get_completed_jobs()
        for job in jobs:
            item_text = f"{job[2]} - {job[1]} (Printer: {job[6]})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, job)
            self.jobs_list.addItem(item)

    def show_job_details(self, item):
        job = item.data(Qt.UserRole)
        job_detail = JobDetailWidget(job, self.db_manager)
        self.detail_area.addWidget(job_detail)
        self.detail_area.setCurrentWidget(job_detail)

# =============================================================================
# JobFormDialog: A dialog to add a new job (with dropdowns).
# =============================================================================
class JobFormDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.job_data = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Add New Job")
        layout = QFormLayout(self)
        self.customer_input = QLineEdit()
        self.job_ticket_input = QLineEdit()
        self.label_type_dropdown = QComboBox()
        self.label_type_dropdown.addItems(LABEL_TYPES)
        self.quantity_input = QSpinBox()
        self.quantity_input.setMaximum(100000)
        self.labels_per_roll_input = QSpinBox()
        self.labels_per_roll_input.setMaximum(10000)
        self.printer_dropdown = QComboBox()
        self.printer_dropdown.addItems(PRINTER_OPTIONS)
        layout.addRow("Customer:", self.customer_input)
        layout.addRow("Job Ticket #:", self.job_ticket_input)
        layout.addRow("Label Type:", self.label_type_dropdown)
        layout.addRow("Quantity:", self.quantity_input)
        layout.addRow("Labels Per Roll:", self.labels_per_roll_input)
        layout.addRow("Printer:", self.printer_dropdown)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        if not self.customer_input.text() or not self.job_ticket_input.text():
            QMessageBox.warning(self, "Input Error", "Customer and Job Ticket # are required.")
            return
        self.job_data = {
            "customer": self.customer_input.text(),
            "job_ticket": self.job_ticket_input.text(),
            "label_type": self.label_type_dropdown.currentText(),
            "quantity": self.quantity_input.value(),
            "labels_per_roll": self.labels_per_roll_input.value(),
            "printer_name": self.printer_dropdown.currentText()
        }
        super().accept()

# =============================================================================
# ReportViewDialog: Displays a detailed, hierarchical report for a completed job.
# =============================================================================
class ReportViewDialog(QDialog):
    def __init__(self, job, db_manager, parent=None):
        super().__init__(parent)
        self.job = job
        self.db_manager = db_manager
        self.setWindowTitle("Detailed Job Report")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        # Job details header
        job_details = QLabel(f"Job Report for {self.job[2]} - {self.job[1]}\n"
                             f"Label Type: {self.job[3]}, Quantity: {self.job[4]}, "
                             f"Labels per Roll: {self.job[5]}, Printer: {self.job[6]}, "
                             f"Created: {self.job[7]}")
        layout.addWidget(job_details)
        # Hierarchical report using QTreeWidget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Roll", "Action", "Note", "Timestamp"])
        layout.addWidget(self.tree)
        # Populate tree with roll tracking data grouped by roll number
        tracking = self.db_manager.get_roll_tracking(self.job[0])
        rolls = {}
        for roll, action, note, timestamp in tracking:
            rolls.setdefault(roll, []).append((action, note, timestamp))
        for roll in sorted(rolls.keys()):
            roll_item = QTreeWidgetItem([str(roll)])
            for action, note, timestamp in rolls[roll]:
                child = QTreeWidgetItem(["", action, note, timestamp])
                roll_item.addChild(child)
            self.tree.addTopLevelItem(roll_item)
        # Download button for report
        download_btn = QPushButton("Download Report")
        download_btn.clicked.connect(self.download_report)
        layout.addWidget(download_btn)
        self.setLayout(layout)

    def download_report(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Report", "", "Text Files (*.txt)")
        if path:
            with open(path, "w") as f:
                f.write(f"Job Report for {self.job[2]} - {self.job[1]}\n")
                f.write(f"Label Type: {self.job[3]}, Quantity: {self.job[4]}, Labels per Roll: {self.job[5]}, Printer: {self.job[6]}, Created: {self.job[7]}\n\n")
                for i in range(self.tree.topLevelItemCount()):
                    roll_item = self.tree.topLevelItem(i)
                    f.write(f"Roll {roll_item.text(0)}:\n")
                    for j in range(roll_item.childCount()):
                        child = roll_item.child(j)
                        f.write(f"  Action: {child.text(1)}, Note: {child.text(2)}, Timestamp: {child.text(3)}\n")
                    f.write("\n")
            QMessageBox.information(self, "Report Saved", f"Report saved to {path}")

# =============================================================================
# DatabaseViewerDialog: Allows exploration and deletion of database entries.
# =============================================================================
class DatabaseViewerDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Database Viewer")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        self.jobs_table = QTableWidget()
        self.rolls_table = QTableWidget()
        self.tab_widget.addTab(self.jobs_table, "Jobs")
        self.tab_widget.addTab(self.rolls_table, "Roll Tracking")
        layout.addWidget(self.tab_widget)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(refresh_btn)
        self.setLayout(layout)
        self.load_data()

    def load_data(self):
        # Load jobs table using column names (index 1)
        jobs = self.db_manager.connection.execute("SELECT * FROM jobs").fetchall()
        header = [desc[1] for desc in self.db_manager.connection.execute("PRAGMA table_info(jobs)").fetchall()]
        self.jobs_table.setColumnCount(len(header))
        self.jobs_table.setRowCount(len(jobs))
        self.jobs_table.setHorizontalHeaderLabels(header)
        for i, row in enumerate(jobs):
            for j, value in enumerate(row):
                self.jobs_table.setItem(i, j, QTableWidgetItem(str(value)))
        # Load roll tracking table using column names (index 1)
        rolls = self.db_manager.connection.execute("SELECT * FROM roll_tracking").fetchall()
        header2 = [desc[1] for desc in self.db_manager.connection.execute("PRAGMA table_info(roll_tracking)").fetchall()]
        self.rolls_table.setColumnCount(len(header2))
        self.rolls_table.setRowCount(len(rolls))
        self.rolls_table.setHorizontalHeaderLabels(header2)
        for i, row in enumerate(rolls):
            for j, value in enumerate(row):
                self.rolls_table.setItem(i, j, QTableWidgetItem(str(value)))

    def delete_selected_job(self):
        selected = self.jobs_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Delete Job", "Please select a job to delete.")
            return
        row = selected[0].row()
        job_id = int(self.jobs_table.item(row, 0).text())
        reply = QMessageBox.question(self, "Confirm Delete", "Delete selected job?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_manager.connection.execute("DELETE FROM jobs WHERE id=?", (job_id,))
            self.db_manager.connection.commit()
            self.load_data()

    def delete_selected_roll(self):
        selected = self.rolls_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Delete Roll", "Please select a roll entry to delete.")
            return
        row = selected[0].row()
        roll_id = int(self.rolls_table.item(row, 0).text())
        reply = QMessageBox.question(self, "Confirm Delete", "Delete selected roll entry?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_manager.connection.execute("DELETE FROM roll_tracking WHERE id=?", (roll_id,))
            self.db_manager.connection.commit()
            self.load_data()

# =============================================================================
# OptionsDialog: Allows adding new label types and printers.
# =============================================================================
class OptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Options / Settings")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Label Types:"))
        self.label_types_list = QListWidget()
        self.label_types_list.addItems(LABEL_TYPES)
        layout.addWidget(self.label_types_list)
        self.new_label_input = QLineEdit()
        self.new_label_input.setPlaceholderText("Add new label type")
        add_label_btn = QPushButton("Add Label Type")
        add_label_btn.clicked.connect(self.add_label_type)
        layout.addWidget(self.new_label_input)
        layout.addWidget(add_label_btn)

        layout.addWidget(QLabel("Printers:"))
        self.printer_list = QListWidget()
        self.printer_list.addItems(PRINTER_OPTIONS)
        layout.addWidget(self.printer_list)
        self.new_printer_input = QLineEdit()
        self.new_printer_input.setPlaceholderText("Add new printer")
        add_printer_btn = QPushButton("Add Printer")
        add_printer_btn.clicked.connect(self.add_printer)
        layout.addWidget(self.new_printer_input)
        layout.addWidget(add_printer_btn)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def add_label_type(self):
        new_label = self.new_label_input.text().strip()
        if new_label and new_label not in LABEL_TYPES:
            LABEL_TYPES.append(new_label)
            self.label_types_list.addItem(new_label)
            self.new_label_input.clear()

    def add_printer(self):
        new_printer = self.new_printer_input.text().strip()
        if new_printer and new_printer not in PRINTER_OPTIONS:
            PRINTER_OPTIONS.append(new_printer)
            self.printer_list.addItem(new_printer)
            self.new_printer_input.clear()

# =============================================================================
# MainWindow: Main UI with tabs for Active and Completed Jobs, and a menu for options.
# =============================================================================
class MainWindow(QMainWindow):
    def __init__(self, db_manager, csv_monitor):
        super().__init__()
        self.db_manager = db_manager
        self.csv_monitor = csv_monitor
        self.active_jobs = {}  # job_id -> JobDetailWidget (persistent)
        self.setWindowTitle("Printer Monitor & Job Manager")
        self.resize(1000, 600)
        self.init_ui()
        self.csv_monitor.update_signal.connect(self.handle_csv_update)

    def init_ui(self):
        # Menu bar
        options_action = QAction("Options", self)
        options_action.triggered.connect(self.open_options)
        db_view_action = QAction("Database Viewer", self)
        db_view_action.triggered.connect(self.open_db_viewer)
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("Settings")
        settings_menu.addAction(options_action)
        settings_menu.addAction(db_view_action)

        central_widget = QWidget()
        main_layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        # Active Jobs Tab
        self.active_tab = QWidget()
        active_layout = QHBoxLayout()
        left_panel = QVBoxLayout()
        self.job_list = QListWidget()
        self.job_list.itemClicked.connect(self.load_job_details)
        left_panel.addWidget(QLabel("Active Jobs"))
        left_panel.addWidget(self.job_list)
        btn_layout = QHBoxLayout()
        add_job_btn = QPushButton("Add New Job")
        add_job_btn.clicked.connect(self.open_job_form)
        edit_job_btn = QPushButton("Edit Job")
        edit_job_btn.clicked.connect(self.edit_job)
        btn_layout.addWidget(add_job_btn)
        btn_layout.addWidget(edit_job_btn)
        left_panel.addLayout(btn_layout)
        active_layout.addLayout(left_panel, 1)
        self.detail_stack = QStackedWidget()
        self.detail_stack.addWidget(QLabel("Select a job to view details."))
        active_layout.addWidget(self.detail_stack, 3)
        self.active_tab.setLayout(active_layout)
        self.tab_widget.addTab(self.active_tab, "Active Jobs")
        # Completed Jobs Tab
        self.completed_tab = CompletedJobsWidget(self.db_manager)
        self.tab_widget.addTab(self.completed_tab, "Completed Jobs")
        main_layout.addWidget(self.tab_widget)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.load_jobs_from_db()

    def load_jobs_from_db(self):
        jobs = self.db_manager.get_active_jobs()
        self.job_list.clear()
        for job in jobs:
            item_text = f"{job[2]} - {job[1]} (Printer: {job[6]})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, job)
            self.job_list.addItem(item)
        self.completed_tab.load_completed_jobs()

    def open_job_form(self):
        dialog = JobFormDialog(self.db_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.job_data
            job_id = self.db_manager.add_job(
                data["customer"], data["job_ticket"], data["label_type"],
                data["quantity"], data["labels_per_roll"], data["printer_name"]
            )
            QMessageBox.information(self, "Job Added", f"Job ID {job_id} has been added.")
            self.load_jobs_from_db()

    def edit_job(self):
        selected_items = self.job_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Edit Job", "Please select a job to edit.")
            return
        job = selected_items[0].data(Qt.UserRole)
        dialog = EditJobDialog(job, self.db_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.job_data
            self.db_manager.update_job(job[0], data["customer"], data["job_ticket"],
                                       data["label_type"], data["quantity"], data["labels_per_roll"], data["printer_name"])
            QMessageBox.information(self, "Job Updated", "Job has been updated.")
            self.load_jobs_from_db()

    def load_job_details(self, item):
        job = item.data(Qt.UserRole)
        job_id = job[0]
        if job_id in self.active_jobs:
            self.detail_stack.setCurrentWidget(self.active_jobs[job_id])
        else:
            job_detail = JobDetailWidget(job, self.db_manager)
            job_detail.job_completed.connect(self.handle_job_completed)
            self.active_jobs[job_id] = job_detail
            self.detail_stack.addWidget(job_detail)
            self.detail_stack.setCurrentWidget(job_detail)

    def handle_csv_update(self, update_data):
        for job_detail in self.active_jobs.values():
            job_detail.update_rolls(update_data)

    def handle_job_completed(self, job_id):
        if job_id in self.active_jobs:
            widget = self.active_jobs.pop(job_id)
            self.detail_stack.removeWidget(widget)
        self.load_jobs_from_db()
        self.completed_tab.load_completed_jobs()

    def open_options(self):
        dialog = OptionsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_jobs_from_db()

    def open_db_viewer(self):
        dialog = DatabaseViewerDialog(self.db_manager, self)
        dialog.exec_()

# =============================================================================
# Main entry point
# =============================================================================
def main():
    # Update the monitored directory as needed
    monitored_dir = r"C:\Users\Encoding 3\Desktop\Encoding Room Printer Tracking\Tracked Encoded EPCS"
    db_path = os.path.join(monitored_dir, "printer_jobs.db")
    if not os.path.exists(monitored_dir):
        os.makedirs(monitored_dir)
    db_manager = DatabaseManager(db_path)
    csv_monitor = WatchdogCSVMonitor(monitored_dir)
    app = QApplication(sys.argv)
    
    # Global StyleSheet for high contrast theme:
    app.setStyleSheet("""
        QMainWindow { background-color: #2d2d30; }
        QWidget { background-color: #2d2d30; color: #ffffff; }
        QPushButton { 
            background-color: #007acc; 
            color: #ffffff; 
            border: 1px solid #005b9f; 
            padding: 5px; 
            border-radius: 4px; 
        }
        QPushButton:hover { background-color: #005b9f; }
        QLineEdit, QTextEdit, QComboBox, QSpinBox { 
            background-color: #3e3e42; 
            color: #ffffff; 
            border: 1px solid #565656; 
            padding: 4px; 
        }
        QProgressBar { 
            border: 1px solid #565656; 
            background-color: #3e3e42; 
            text-align: center; 
            color: #ffffff; 
        }
        QProgressBar::chunk { background-color: #007acc; }
        QTreeWidget, QListWidget, QTableWidget { 
            background-color: #3e3e42; 
            color: #ffffff; 
            border: 1px solid #565656; 
        }
        QLabel { font-size: 12pt; }
    """)
    
    main_win = MainWindow(db_manager, csv_monitor)
    main_win.show()
    csv_monitor.start()
    try:
        sys.exit(app.exec_())
    finally:
        csv_monitor.stop()

if __name__ == '__main__':
    main()
