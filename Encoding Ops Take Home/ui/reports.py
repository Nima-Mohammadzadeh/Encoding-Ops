# ===== reports.py =====

from PyQt6.QtWidgets import *

class ReportsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Job/Date:"))
        self.filter_input = QLineEdit()
        filter_layout.addWidget(self.filter_input)
        layout.addLayout(filter_layout)
        csv_btn = QPushButton("Download CSV")
        csv_btn.clicked.connect(lambda: QMessageBox.information(self, "Download", "CSV downloaded (mock)."))
        pdf_btn = QPushButton("Download PDF")
        pdf_btn.clicked.connect(lambda: QMessageBox.information(self, "Download", "PDF downloaded (mock)."))
        layout.addWidget(csv_btn)
        layout.addWidget(pdf_btn)
        self.setLayout(layout)