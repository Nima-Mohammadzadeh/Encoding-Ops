from PyQt6.QtWidgets import *
from jobdata import JobData
import random

class TestPrintStep(QWidget):
    def __init__(self, job: JobData):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Test Print & Signoff"))
        print_btn = QPushButton("Print 5")
        print_btn.clicked.connect(self.print_labels)
        layout.addWidget(print_btn)
        self.result_list = QListWidget()
        layout.addWidget(self.result_list)
        sign_btn = QPushButton("Digital Signoff")
        sign_btn.clicked.connect(self.sign_off)
        layout.addWidget(sign_btn)
        self.setLayout(layout)
    def print_labels(self):
        self.result_list.clear()
        for i in range(5):
            self.result_list.addItem(f"Label {i+1}: EPC {random.randint(10000,99999)} - PASS")
        QMessageBox.information
        QMessageBox.information(self, "Printed", "Test print (mock)")
    def sign_off(self):
        QMessageBox.information(self, "Signoff", "Test print signed off (mock)")
