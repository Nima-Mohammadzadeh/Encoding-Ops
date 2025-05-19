# ===== database_tab.py =====

# database_tab.py
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import os
import pandas as pd




class DatabaseFileWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, data_folder, db_path):
        super().__init__()
        self.data_folder = data_folder
        self.db_path = db_path

    def run(self):
        import pandas as pd
        import os
        try:
            os.makedirs(self.data_folder, exist_ok=True)
            df = pd.DataFrame(columns=["EPC", "Serial", "UPC", "Date"])
            df.to_excel(self.db_path, index=False)
            self.finished.emit(self.db_path)
        except Exception as e:
            self.error.emit(str(e))

class DatabaseTab(QWidget):
    def __init__(self, job):
        super().__init__()
        self.job = job
        layout = QVBoxLayout()
        self.info_label = QLabel("No database present.\nClick below to generate a new EPC database.")
        layout.addWidget(self.info_label)
        self.gen_btn = QPushButton("Generate Database File")
        self.gen_btn.clicked.connect(self.handle_generate_db)
        layout.addWidget(self.gen_btn)
        self.setLayout(layout)
        
        
        
    def handle_generate_db(self):
        job_folder = getattr(self.job, 'folder_path', None)
        if not job_folder:
            QMessageBox.warning(self, "Error", "No job folder found.")
            return
        data_folder = os.path.join(job_folder, "Data")
        db_path = os.path.join(data_folder, "EPC_Database.xlsx")
        self.progress = QProgressDialog(
            "Generating database file...", None, 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress.setAutoClose(False)
        self.progress.setAutoReset(False)
        self.progress.show()

        self.worker_thread = QThread(self)
        self.worker = DatabaseFileWorker(data_folder, db_path)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_db_gen_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker.error.connect(self.on_db_gen_error)
        self.worker_thread.start()

    def on_db_gen_finished(self, db_path):
        self.progress.close()
        QMessageBox.information(self, "Database Created", f"Database saved at:\n{db_path}")
        self.info_label.setText(f"Database created at: {db_path}")

    def on_db_gen_error(self, err):
        self.progress.close()
        QMessageBox.critical(self, "Database Error", f"Database generation failed:\n{err}")

