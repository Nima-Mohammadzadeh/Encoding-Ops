from PyQt6.QtWidgets import *
from data.jobdata import JobData


class RollTrackerStep(QWidget):
    def __init__(self, job: JobData, segments=3):
        super().__init__()
        layout = QVBoxLayout()
        qty = job.qty
        segment_size = qty // segments if segments else qty
        layout.addWidget(QLabel(f"Total: {qty} | Rolls: {segments}"))
        for roll in range(1, segments+1):
            bar = QProgressBar()
            val = (segment_size / qty * 100) if roll < segments else (
                ((qty - (segments-1)*segment_size)/qty)*100)
            bar.setValue(int(val))
            bar.setFormat(f"Roll {roll}: {segment_size} labels")
            layout.addWidget(bar)
        export_btn = QPushButton("Export Roll Tracker")
        export_btn.clicked.connect(lambda: QMessageBox.information(self, "PDF", "Exported roll tracker (mock)"))
        layout.addWidget(export_btn)
        self.setLayout(layout)