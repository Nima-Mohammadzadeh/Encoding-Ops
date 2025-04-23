from PyQt6.QtWidgets import *
from jobdata import JobData

class DocsExportStep(QWidget):
    def __init__(self, job: JobData):
        super().__init__()
        self.job = job
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Export Docs/Archive Job"))
        pdf_btn = QPushButton("Export as PDF")
        pdf_btn.clicked.connect(lambda: QMessageBox.information(self, "PDF", "Job docs exported (mock)"))
        finish_btn = QPushButton("Mark Complete")
        finish_btn.clicked.connect(self.finish_job)
        layout.addWidget(pdf_btn)
        layout.addWidget(finish_btn)
        self.setLayout(layout)
    def finish_job(self):
        self.job.status = "Complete"
        QMessageBox.information(self, "Done", "Job marked complete (mock).")
