from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy, QFrame, QVBoxLayout
from PyQt6.QtGui import QFont, QIcon, QPainter, QPen, QBrush, QLinearGradient, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPointF
from theme_manager import THEME_MANAGER

class ScreenshotNavButton(QPushButton):
    """Navigation button matching the screenshot's style"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.is_active = False
        self.setFixedHeight(50)
        self.setMinimumWidth(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def set_active(self, active):
        self.is_active = active
        self.update()

class ScreenshotBrandLabel(QLabel):
    """Brand label matching the screenshot's "RFID Workflow Manager" style"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("RFID Workflow Manager")
        font = QFont("Segoe UI", 13, QFont.Weight.Bold)
        self.setFont(font)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

class ScreenshotActionIcon(QPushButton):
    """Action icon buttons matching the screenshot's right-side icons"""
    def __init__(self, icon_text, tooltip="", parent=None):
        super().__init__(icon_text, parent)
        self.setFixedSize(35, 35)
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

class NavigationBar(QWidget):
    # Define signals for each navigation button
    navigateDashboard = pyqtSignal()
    navigateJobs = pyqtSignal()
    navigateLabels = pyqtSignal()
    navigateReports = pyqtSignal()
    navigateSettings = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_active_button = None
        self.setup_ui()
        THEME_MANAGER.register_for_theme_updates(self.update_theme_stylesheet)
        self.update_theme_stylesheet()

    def setup_ui(self):
        self.setFixedWidth(220)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.brand_label = ScreenshotBrandLabel()
        layout.addWidget(self.brand_label)
        
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(10)

        self.dashboard_button = ScreenshotNavButton("Dashboard")
        self.jobs_button = ScreenshotNavButton("Jobs")
        self.labels_button = ScreenshotNavButton("Labels")
        self.reports_button = ScreenshotNavButton("Reports")
        self.settings_button = ScreenshotNavButton("Settings")

        self.dashboard_button.clicked.connect(lambda: self.on_nav_clicked(self.dashboard_button, self.navigateDashboard))
        self.jobs_button.clicked.connect(lambda: self.on_nav_clicked(self.jobs_button, self.navigateJobs))
        self.labels_button.clicked.connect(lambda: self.on_nav_clicked(self.labels_button, self.navigateLabels))
        self.reports_button.clicked.connect(lambda: self.on_nav_clicked(self.reports_button, self.navigateReports))
        self.settings_button.clicked.connect(lambda: self.on_nav_clicked(self.settings_button, self.navigateSettings))

        nav_layout.addWidget(self.dashboard_button)
        nav_layout.addWidget(self.jobs_button)
        nav_layout.addWidget(self.labels_button)
        nav_layout.addWidget(self.reports_button)
        nav_layout.addWidget(self.settings_button)
        
        layout.addWidget(nav_container)

        layout.addStretch()

        actions_container = QWidget()
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(15)
        actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.notification_button = ScreenshotActionIcon("🔔", "Notifications")
        self.user_profile_button = ScreenshotActionIcon("👤", "User Profile")

        actions_layout.addWidget(self.notification_button)
        actions_layout.addWidget(self.user_profile_button)

        layout.addWidget(actions_container)

        self.on_nav_clicked(self.dashboard_button, None)

    def on_nav_clicked(self, button, signal):
        if self.current_active_button:
            self.current_active_button.set_active(False)
        
        button.set_active(True)
        self.current_active_button = button
        self.update_theme_stylesheet()
        
        if signal:
            signal.emit()

    def update_theme_stylesheet(self):
        theme = THEME_MANAGER.current()
        
        self.setStyleSheet(f"""
            NavigationBar {{
                background-color: {theme["SIDEBAR_BACKGROUND"] if "SIDEBAR_BACKGROUND" in theme else theme["WINDOW_BACKGROUND"]};
                border-right: 1px solid {theme["BORDER_COLOR"]};
            }}
        """)
        
        self.brand_label.setStyleSheet(f"""
            QLabel {{
                color: {theme["PRIMARY_TEXT"]};
                background-color: transparent;
                padding-bottom: 10px;
                padding-top: 5px;
            }}
        """)
        
        nav_button_style = f"""
            ScreenshotNavButton {{
                background-color: transparent;
                color: {theme["SECONDARY_TEXT"]};
                border: none;
                padding: 10px 15px;
                font-size: 11pt;
                font-weight: 500;
                border-radius: 6px;
                text-align: left;
            }}
            
            ScreenshotNavButton:hover {{
                background-color: {theme["NAV_ITEM_HOVER_BACKGROUND"]};
                color: {theme["PRIMARY_TEXT"]};
            }}
        """
        
        for button in [self.dashboard_button, self.jobs_button, self.labels_button, self.reports_button, self.settings_button]:
            if button == self.current_active_button:
                button.setStyleSheet(f"""
                    ScreenshotNavButton {{
                        background-color: {theme["PRIMARY_ACCENT"]};
                        color: {theme["PRIMARY_ACCENT_TEXT"]};
                        border: none;
                        padding: 10px 15px;
                        font-size: 11pt;
                        font-weight: 600;
                        border-radius: 6px;
                        text-align: left;
                    }}
                    
                    ScreenshotNavButton:hover {{
                        background-color: {theme["PRIMARY_ACCENT_HOVER"]};
                        color: {theme["PRIMARY_ACCENT_TEXT"]};
                    }}
                """)
            else:
                button.setStyleSheet(nav_button_style)
        
        action_icon_style = f"""
            ScreenshotActionIcon {{
                background-color: transparent;
                border: none;
                border-radius: 17px;
                font-size: 16px;
                color: {theme["SECONDARY_TEXT"]};
            }}
            
            ScreenshotActionIcon:hover {{
                background-color: {theme["NAV_ITEM_HOVER_BACKGROUND"]};
                color: {theme["PRIMARY_TEXT"]};
            }}
            
            ScreenshotActionIcon:pressed {{
                background-color: {theme["PRIMARY_ACCENT"]};
                color: {theme["PRIMARY_ACCENT_TEXT"]};
            }}
        """
        
        self.notification_button.setStyleSheet(action_icon_style)
        self.user_profile_button.setStyleSheet(action_icon_style)

    def __del__(self):
        THEME_MANAGER.unregister_for_theme_updates(self.update_theme_stylesheet)

if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    nav_bar = NavigationBar()
    nav_bar.show()
    sys.exit(app.exec()) 