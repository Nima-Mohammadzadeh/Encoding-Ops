# database_tab.py
from PyQt6.QtWidgets import *
import os
import pandas as pd

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
        os.makedirs(data_folder, exist_ok=True)
        db_path = os.path.join(data_folder, "EPC_Database.xlsx")
        # Change the columns as needed for your project:
        df = pd.DataFrame(columns=["EPC", "Serial", "UPC", "Date"])
        df.to_excel(db_path, index=False)
        QMessageBox.information(self, "Database Created", f"Database saved at:\n{db_path}")
        self.info_label.setText(f"Database created at: {db_path}")