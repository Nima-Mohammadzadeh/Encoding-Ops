# module_selector.py

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QHBoxLayout, QLabel

class ModuleSelectionDialog(QDialog):
    """
    Dialog asking which workflow modules to use for a new job.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Workflow Modules")
        layout = QVBoxLayout()
        msg = QLabel(
            "Choose which modules to use for this job.\n"
            "You can choose any combination, but at least one."
        )
        layout.addWidget(msg)
        self.cb_checklist = QCheckBox("Encoding Checklist")
        self.cb_dbgen = QCheckBox("Database Generator")
        self.cb_rolltracker = QCheckBox("Roll Tracker")
        self.cb_checklist.setChecked(True)
        self.cb_dbgen.setChecked(False)
        self.cb_rolltracker.setChecked(False)
        layout.addWidget(self.cb_checklist)
        layout.addWidget(self.cb_dbgen)
        layout.addWidget(self.cb_rolltracker)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Start Workflow")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

    def get_selection(self):
        return {
            "show_checklist": self.cb_checklist.isChecked(),
            "show_dbgen": self.cb_dbgen.isChecked(),
            "show_rolltracker": self.cb_rolltracker.isChecked()
        }