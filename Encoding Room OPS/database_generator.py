from PyQt6.QtWidgets import *
import csv
from config import SERIALS_CSV_PATH
from util import update_latest_serial
from jobdata import JobData

class DatabaseGeneratorTab(QWidget):
    def __init__(self, job: JobData):
        super().__init__()
        self.job = job
        layout = QVBoxLayout()
        info_lbl = QLabel("Serial numbers in use are listed below.\n"
                          "Enter a new serial or range to check and append if unique.")
        layout.addWidget(info_lbl)
        self.table = QTableWidget()
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(['Serial Number'])
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        self.refresh_table()
        frm = QFormLayout()
        self.serial_input = QLineEdit()
        self.range_input = QLineEdit()
        save_btn = QPushButton("Add Serial(s)")
        save_btn.clicked.connect(self.try_save_serials)
        frm.addRow("Single Serial:", self.serial_input)
        frm.addRow("Or Serial Range (start-end):", self.range_input)
        frm.addRow(save_btn)
        layout.addLayout(frm)
        self.setLayout(layout)
    def refresh_table(self):
        serials = self.get_csv_serials()
        self.table.setRowCount(len(serials))
        for idx, s in enumerate(serials):
            item = QTableWidgetItem(s)
            self.table.setItem(idx, 0, item)
    @staticmethod
    def get_csv_serials():
        # Returns list of strings, skipping the header
        try:
            with open(SERIALS_CSV_PATH, newline='') as f:
                reader = csv.reader(f)
                next(reader, None)  # header
                return [x[0] for x in reader]
        except Exception:
            return []
    def try_save_serials(self):
        current_serials = set(self.get_csv_serials())
        added = []
        # Single
        val = self.serial_input.text().strip()
        if val:
            if val in current_serials:
                QMessageBox.warning(self, "Duplicate", f"Serial {val} already exists.")
                return
            added.append(val)
        # Range
        range_val = self.range_input.text().strip()
        if range_val:
            try:
                start, end = [x.strip() for x in range_val.split('-')]
                start, end = int(start), int(end)
                candidate = [str(s) for s in range(start, end+1)]
                duplicates = [s for s in candidate if s in current_serials]
                if duplicates:
                    QMessageBox.warning(self, "Duplicate", f"These serials already exist: {', '.join(duplicates)}")
                    return
                added.extend(candidate)
            except Exception:
                QMessageBox.warning(self, "Error", "Serial range format must be start-end (e.g. 1000-1010)")
                return
        if not added:
            QMessageBox.information(self, "None", "Nothing to add.")
            return
        # Append
        with open(SERIALS_CSV_PATH, 'a', newline='') as f:
            writer = csv.writer(f)
            for s in added:
                writer.writerow([s])
        if added:           
            last_serial = int(added[-1])  # serials were str but numeric
            update_latest_serial(last_serial + 1)        
        self.refresh_table()
        QMessageBox.information(self, "Saved", f"Saved {len(added)} serials. They are now reserved.")
        
