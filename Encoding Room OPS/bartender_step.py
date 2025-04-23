from PyQt6.QtWidgets import *
from jobdata import JobData

class BarTenderStep(QWidget):
    def __init__(self, job: JobData):
        super().__init__()
        self.job = job
        layout = QFormLayout()
        self.template_path = QLineEdit()
        browse_template = QPushButton("Browse Template")
        browse_template.clicked.connect(self.browse_template)
        self.dest_path = QLineEdit()
        browse_dest = QPushButton("Browse Dest")
        browse_dest.clicked.connect(self.browse_dest)
        layout.addRow("Template File:", self.template_path)
        layout.addRow("", browse_template)
        layout.addRow("Destination Path:", self.dest_path)
        layout.addRow("", browse_dest)
        link_btn = QPushButton("Link File")
        link_btn.clicked.connect(self.link_file)
        layout.addRow(link_btn)
        self.setLayout(layout)
    def browse_template(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select .btw Template", "", "BarTender Files (*.btw)")
        if path:
            self.template_path.setText(path)
    def browse_dest(self):
        path = QFileDialog.getExistingDirectory(self, "Select Destination")
        if path:
            self.dest_path.setText(path)
    def link_file(self):
        self.job.bartender_file = self.template_path.text()
        QMessageBox.information(self, "Success", "BarTender file linked (mock).")
