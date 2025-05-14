from PyQt6.QtWidgets import *
from PyQt6.QtCore import QObject, pyqtSignal, QThread

import csv
from config import SERIALS_CSV_PATH
from util import update_latest_serial
from data.jobdata import JobData




class SerialAppendWorker(QObject):
    finished = pyqtSignal(int)   # last serial written
    error = pyqtSignal(str)

    def __init__(self, serials):
        super().__init__()
        self.serials = serials

    def run(self):
        import csv
        from util import SERIALS_CSV_PATH, update_latest_serial
        try:
            with open(SERIALS_CSV_PATH, 'a', newline='') as f:
                writer = csv.writer(f)
                for s in self.serials:
                    writer.writerow([s])
            if self.serials:
                last_serial = int(self.serials[-1])
                update_latest_serial(last_serial + 1)
            self.finished.emit(last_serial)
        except Exception as ex:
            self.error.emit(str(ex))

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
        self.progress = QProgressDialog("Saving serials...", None, 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress.show()
        self.serials_thread = QThread(self)
        self.serials_worker = SerialAppendWorker(added)
        self.serials_worker.moveToThread(self.serials_thread)
        self.serials_thread.started.connect(self.serials_worker.run)
        self.serials_worker.finished.connect(self.on_serial_save_finished)
        self.serials_worker.finished.connect(self.serials_thread.quit)
        self.serials_worker.finished.connect(self.serials_worker.deleteLater)
        self.serials_thread.finished.connect(self.serials_thread.deleteLater)
        self.serials_worker.error.connect(self.on_serial_save_error)
        self.serials_thread.start()
        
    def on_serial_save_finished(self, last_serial):
        self.progress.close()
        self.refresh_table()
        QMessageBox.information(self, "Saved", f"Saved serials. Up to {last_serial} now reserved.")

    def on_serial_save_error(self, msg):
        self.progress.close()
        QMessageBox.critical(self, "Error", f"Serial save error:\n{msg}")

