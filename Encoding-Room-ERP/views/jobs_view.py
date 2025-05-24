from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from theme_manager import THEME_MANAGER

class JobsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        THEME_MANAGER.register_for_theme_updates(self.update_theme_stylesheet)
        self.update_theme_stylesheet()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Title
        title = QLabel("Job Management")
        title.setObjectName("pageTitle")
        title_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        title.setFont(title_font)
        layout.addWidget(title)

        # Description
        description = QLabel(
            "Manage RFID workflow jobs, track progress, and monitor completion status. "
            "Create new jobs, assign tasks, and review job history and performance metrics."
        )
        description.setObjectName("pageDescription")
        desc_font = QFont("Segoe UI", 12)
        description.setFont(desc_font)
        description.setWordWrap(True)
        layout.addWidget(description)

        layout.addStretch()

    def update_theme_stylesheet(self):
        theme = THEME_MANAGER.current()
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme["WINDOW_BACKGROUND"]};
            }}
            QLabel#pageTitle {{
                color: {theme["PRIMARY_TEXT"]};
                margin-bottom: 10px;
            }}
            QLabel#pageDescription {{
                color: {theme["SECONDARY_TEXT"]};
                line-height: 1.4;
            }}
        """)

    def __del__(self):
        THEME_MANAGER.unregister_for_theme_updates(self.update_theme_stylesheet) 