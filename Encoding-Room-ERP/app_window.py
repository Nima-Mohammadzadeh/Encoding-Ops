from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QStackedWidget, QApplication, QHBoxLayout
from PyQt6.QtGui import QIcon, QFont
# Removed Qt and QLabel as they are not directly used now in this scope or handled by imported widgets

# Import the actual views
from views.dashboard_view import DashboardView
from views.jobs_view import JobsView
from views.labels_view import LabelsView  # Import the new LabelsView
from views.settings_view import SettingsView
from views.reports_view import ReportsView # Import ReportsView

# Import the NavigationBar
from navigation_bar import NavigationBar
from theme_manager import THEME_MANAGER # Import ThemeManager

class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RFID Workflow Manager")  # Update title to match screenshot
        # self.setWindowIcon(QIcon("path/to/your/icon.png")) # Add icon later
        self.setGeometry(100, 100, 1280, 720) # Adjusted size

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)

        # Navigation Bar (now a sidebar)
        self.nav_bar = NavigationBar()
        self.main_layout.addWidget(self.nav_bar)

        # Content area where views will be switched
        self.content_area = QStackedWidget()
        self.main_layout.addWidget(self.content_area)

        # Initialize and add views
        self.dashboard_view = DashboardView() # Instantiate DashboardView
        self.jobs_view = JobsView()
        self.labels_view = LabelsView()  # Use the new LabelsView
        self.settings_view = SettingsView()
        self.reports_view = ReportsView() # Instantiate ReportsView

        self.content_area.addWidget(self.dashboard_view) # Index 0
        self.content_area.addWidget(self.jobs_view)      # Index 1
        self.content_area.addWidget(self.labels_view)    # Index 2
        self.content_area.addWidget(self.reports_view)   # Index 3
        self.content_area.addWidget(self.settings_view)  # Index 4
        
        # Connect navigation signals to switch views
        self.nav_bar.navigateDashboard.connect(lambda: self.switch_view(0)) # Connect Dashboard
        self.nav_bar.navigateJobs.connect(lambda: self.switch_view(1))
        self.nav_bar.navigateLabels.connect(lambda: self.switch_view(2))
        self.nav_bar.navigateReports.connect(lambda: self.switch_view(3)) # Connect Reports
        self.nav_bar.navigateSettings.connect(lambda: self.switch_view(4))

        # Set initial view to Dashboard (index 0)
        self.switch_view(0) # Show Dashboard by default

        THEME_MANAGER.register_for_theme_updates(self.update_theme_stylesheet)
        self.update_theme_stylesheet() # Apply initial theme

    def update_theme_stylesheet(self):
        theme = THEME_MANAGER.current()
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme["WINDOW_BACKGROUND"]};
            }}
            QStackedWidget {{
                background-color: {theme["WINDOW_BACKGROUND"]}; /* Match window background */
            }}
        """)
        # Also explicitly set palette for the central widget to ensure propagation
        # as QMainWindow might not propagate its own palette deeply enough for all cases.
        # palette = QPalette()
        # palette.setColor(QPalette.ColorRole.Window, QColor(theme["WINDOW_BACKGROUND"]))
        # self.central_widget.setPalette(palette)
        # self.central_widget.setAutoFillBackground(True)

    def switch_view(self, index):
        self.content_area.setCurrentIndex(index)

    def __del__(self):
        THEME_MANAGER.unregister_for_theme_updates(self.update_theme_stylesheet)

if __name__ == '__main__':
    import sys
    # QApplication is already imported at the top
    app = QApplication(sys.argv)
    
    # Global font should be set here as before
    default_font = QFont()
    default_font.setFamily("Segoe UI")
    default_font.setPointSize(10)
    app.setFont(default_font)

    # Apply initial theme to the application instance (QPalette)
    THEME_MANAGER.apply_theme_to_app() 

    window = AppWindow()
    window.show()
    sys.exit(app.exec()) 