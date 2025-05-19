from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout

class JobListItemWidget(QWidget):
    def __init__(self, job_name, remove_callback, complete_callback=None, is_completed=False):
        super().__init__()
        layout = QHBoxLayout()
        self.label = QLabel(job_name)
        layout.addWidget(self.label)
        layout.addStretch()
        if not is_completed:
            if complete_callback:
                self.complete_btn = QPushButton('✓')
                self.complete_btn.setToolTip("Mark as Completed")
                self.complete_btn.setFixedSize(22, 22)
                self.complete_btn.setStyleSheet("QPushButton { border: none; color: #080; }")
                self.complete_btn.clicked.connect(complete_callback)
                layout.addWidget(self.complete_btn)
            self.remove_btn = QPushButton("✖")
            self.remove_btn.setFixedSize(22, 22)
            self.remove_btn.setStyleSheet("QPushButton { border: none; color: #B00; }")
            self.remove_btn.clicked.connect(remove_callback)
            layout.addWidget(self.remove_btn)
        self.setLayout(layout)