import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont # Import QFont
from app_window import AppWindow # Import the new AppWindow

def main():
    app = QApplication(sys.argv)
    
    # Set global font
    default_font = QFont()
    default_font.setFamily("Segoe UI") # Modern, clean font
    default_font.setPointSize(10)      # Adjust as needed
    app.setFont(default_font)
    
    window = AppWindow() # Create an instance of AppWindow
    window.show()
        
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 