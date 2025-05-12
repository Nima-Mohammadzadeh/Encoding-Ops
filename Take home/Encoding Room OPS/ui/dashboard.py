from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QTimer, Qt
from util import current_time_str
import random

# ---------- Dashboard ----------
class PrinterDetailDialog(QDialog):
    def __init__(self, printer_data):
        super().__init__()
        self.setWindowTitle(f"Details for {printer_data['printer_id']}")
        self.resize(400, 300)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Printer Name: {printer_data['printer_id']}"))
        printed = printer_data["pass_count"] + printer_data["fail_count"]
        layout.addWidget(QLabel(f"Total Printed: {printed}"))
        layout.addWidget(QLabel(f"Total Voided: {printer_data['fail_count']}"))
        error_pct = f"{(printer_data['fail_count']/printed * 100):.1f}%" if printed > 0 else "0%"
        layout.addWidget(QLabel(f"Quality Error %: {error_pct}"))
        layout.addWidget(QLabel(f"Last Update: {printer_data['last_event']}"))
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        self.setLayout(layout)

class DashboardWidget(QWidget):
    def __init__(self, printer_data):
        super().__init__()
        self.all_printers = printer_data
        main_layout = QVBoxLayout()
        header_layout = QHBoxLayout()
        header_label = QLabel("Dashboard / Live Monitor")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        self.interval_selector = QComboBox()
        self.interval_selector.addItems(["Live", "1 hour", "4 hours", "8 hours"])
        header_layout.addWidget(QLabel("Interval:"))
        header_layout.addWidget(self.interval_selector)
        main_layout.addLayout(header_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Printer", "Printed", "Voided", "Error %"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        font = QFont()
        font.setPointSize(11)
        self.table.setFont(font)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.cellDoubleClicked.connect(self.handle_row_click)
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)
        self.populate_table()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_table_data)
        self.timer.start(3000)
    def populate_table(self):
        printers = sorted(self.all_printers.keys())
        self.table.setRowCount(len(printers))
        for idx, pid in enumerate(printers):
            data = self.all_printers[pid]
            printed = data["pass_count"] + data["fail_count"]
            voided = data["fail_count"]
            error_pct = f"{(voided/printed * 100):.1f}%" if printed > 0 else "0%"
            self.table.setItem(idx, 0, QTableWidgetItem(pid))
            self.table.setItem(idx, 1, QTableWidgetItem(str(printed)))
            self.table.setItem(idx, 2, QTableWidgetItem(str(voided)))
            self.table.setItem(idx, 3, QTableWidgetItem(error_pct))
    def update_table_data(self):
        interval = self.interval_selector.currentText()
        multiplier = {"Live": 1, "1 hour": 1, "4 hours": 2, "8 hours": 3}.get(interval, 1)
        for pid in self.all_printers:
            data = self.all_printers[pid]
            data["pass_count"] += random.randint(0, 5 * multiplier)
            data["fail_count"] += random.randint(0, 3 * multiplier)
            data["last_event"] = current_time_str()
        self.populate_table()
    def handle_row_click(self, row, column):
        pid_item = self.table.item(row, 0)
        if pid_item:
            pid = pid_item.text()
            printer_data = self.all_printers.get(pid)
            if printer_data:
                dlg = PrinterDetailDialog(printer_data)
                dlg.exec()