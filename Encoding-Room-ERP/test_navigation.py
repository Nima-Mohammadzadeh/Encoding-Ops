#!/usr/bin/env python3
"""
Test script to showcase the new navigation bar design
"""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from navigation_bar import NavigationBar
from theme_manager import THEME_MANAGER

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Navigation Bar Test - Encoding Room ERP")
        self.setGeometry(200, 200, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add navigation bar
        self.nav_bar = NavigationBar()
        layout.addWidget(self.nav_bar)
        
        # Add content area for demonstration
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Demo content
        title_label = QLabel("🎉 Navigation Bar Revamped!")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: bold;
                color: #007bff;
                margin: 50px;
            }
        """)
        
        features_label = QLabel("""
        ✨ New Features:
        • Modern gradient logo with "Encoding Room ERP" branding
        • Pill-shaped navigation buttons with active states
        • Enhanced action icons with tooltips
        • Improved spacing and visual hierarchy
        • Better theme integration (try the theme toggle!)
        • Professional visual separator between sections
        • Consistent design language throughout
        """)
        features_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        features_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                line-height: 1.6;
                color: #495057;
                background-color: #f8f9fa;
                padding: 30px;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        content_layout.addWidget(title_label)
        content_layout.addWidget(features_label)
        
        layout.addWidget(content_area)
        
        # Connect navigation signals for demo
        self.nav_bar.navigateDashboard.connect(lambda: self.show_message("Dashboard"))
        self.nav_bar.navigateJobs.connect(lambda: self.show_message("Jobs"))
        self.nav_bar.navigateReports.connect(lambda: self.show_message("Reports"))
        self.nav_bar.navigateSettings.connect(lambda: self.show_message("Settings"))
        
        # Apply theme
        THEME_MANAGER.register_for_theme_updates(self.update_theme)
        self.update_theme()
    
    def show_message(self, section):
        print(f"🔄 Navigated to: {section}")
    
    def update_theme(self):
        theme = THEME_MANAGER.current()
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme["WINDOW_BACKGROUND"]};
            }}
        """)

def main():
    app = QApplication(sys.argv)
    
    # Set global font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Apply initial theme
    THEME_MANAGER.apply_theme_to_app()
    
    window = TestWindow()
    window.show()
    
    print("🚀 Navigation Bar Test Window Opened!")
    print("💡 Try clicking the navigation buttons and theme toggle!")
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 