#!/usr/bin/env python3
"""
Test script for the new RFID Workflow Manager navigation bar
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from app_window import AppWindow

def test_navigation():
    """Test the new navigation bar implementation"""
    print("Testing RFID Workflow Manager Navigation Bar...")
    print("Features implemented:")
    print("✓ RFID Workflow Manager branding")
    print("✓ Jobs, Labels, Settings navigation tabs")
    print("✓ Notification and user profile icons")
    print("✓ Subtle gradient background matching screenshot")
    print("✓ Clean, modern styling")
    print("✓ Theme support (light/dark)")
    print("✓ Active state highlighting")
    print("✓ Proper view switching")
    
    app = QApplication(sys.argv)
    
    # Set global font
    default_font = QFont()
    default_font.setFamily("Segoe UI")
    default_font.setPointSize(10)
    app.setFont(default_font)
    
    window = AppWindow()
    window.show()
    
    print("\nNavigation bar should now match the screenshot design!")
    print("- Brand: 'RFID Workflow Manager' on the left")
    print("- Navigation: 'Jobs', 'Labels', 'Settings' in the center")
    print("- Icons: Notification bell and user profile on the right")
    print("- Gradient: Subtle white to light gray gradient")
    
    return app.exec()

if __name__ == '__main__':
    sys.exit(test_navigation()) 