from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from theme_manager import THEME_MANAGER

class SettingsView(QWidget):
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
        title = QLabel("Settings")
        title.setObjectName("pageTitle")
        title_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        title.setFont(title_font)
        layout.addWidget(title)

        # Description
        description = QLabel(
            "Configure RFID Workflow Manager settings, preferences, and system configurations."
        )
        description.setObjectName("pageDescription")
        desc_font = QFont("Segoe UI", 12)
        description.setFont(desc_font)
        description.setWordWrap(True)
        layout.addWidget(description)

        # Theme Toggle Section
        theme_section = QFrame()
        theme_section.setObjectName("settingsSection")
        theme_layout = QVBoxLayout(theme_section)
        theme_layout.setContentsMargins(20, 20, 20, 20)
        theme_layout.setSpacing(10)

        theme_title = QLabel("Appearance")
        theme_title.setObjectName("sectionTitle")
        theme_title_font = QFont("Segoe UI", 16, QFont.Weight.DemiBold)
        theme_title.setFont(theme_title_font)
        theme_layout.addWidget(theme_title)

        theme_controls = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_label.setObjectName("settingLabel")
        self.theme_toggle_button = QPushButton("Switch to Dark Mode")
        self.theme_toggle_button.setObjectName("themeToggleButton")
        self.theme_toggle_button.clicked.connect(self.toggle_theme)
        
        theme_controls.addWidget(theme_label)
        theme_controls.addWidget(self.theme_toggle_button)
        theme_controls.addStretch()
        
        theme_layout.addLayout(theme_controls)
        layout.addWidget(theme_section)

        layout.addStretch()

    def toggle_theme(self):
        THEME_MANAGER.toggle_theme()
        # Update button text
        if THEME_MANAGER.current_theme_name == "dark":
            self.theme_toggle_button.setText("Switch to Light Mode")
        else:
            self.theme_toggle_button.setText("Switch to Dark Mode")

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
            QFrame#settingsSection {{
                background-color: {theme["CONTENT_BACKGROUND"]};
                border: 1px solid {theme["BORDER_COLOR"]};
                border-radius: 8px;
            }}
            QLabel#sectionTitle {{
                color: {theme["PRIMARY_TEXT"]};
                margin-bottom: 5px;
            }}
            QLabel#settingLabel {{
                color: {theme["SECONDARY_TEXT"]};
            }}
            QPushButton#themeToggleButton {{
                background-color: {theme["PRIMARY_ACCENT"]};
                color: {theme["PRIMARY_ACCENT_TEXT"]};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            QPushButton#themeToggleButton:hover {{
                background-color: {theme["PRIMARY_ACCENT_HOVER"]};
            }}
            QPushButton#themeToggleButton:pressed {{
                background-color: {theme["PRIMARY_ACCENT_PRESSED"]};
            }}
        """)

        # Update button text based on current theme
        if THEME_MANAGER.current_theme_name == "dark":
            self.theme_toggle_button.setText("Switch to Light Mode")
        else:
            self.theme_toggle_button.setText("Switch to Dark Mode")

    def __del__(self):
        THEME_MANAGER.unregister_for_theme_updates(self.update_theme_stylesheet) 