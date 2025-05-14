from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl

import sys, tempfile, shutil

PDF_PATH = r"C:\Users\Encoding 3\Desktop\Encoding Checklist V4.1.pdf"  # Use any simple, known-good PDF

app = QApplication(sys.argv)
w = QWebEngineView()
temp_pdf = tempfile.gettempdir() + r"\test_embedded.pdf"
shutil.copy2(PDF_PATH, temp_pdf)
w.setUrl(QUrl.fromLocalFile(temp_pdf))
w.resize(800, 600)
w.show()
sys.exit(app.exec())