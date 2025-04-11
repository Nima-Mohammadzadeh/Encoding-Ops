import sys, random, datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFormLayout, QMessageBox, QFileDialog,
    QTabWidget, QProgressBar, QListWidget, QComboBox, QToolBar, QDialog,
    QScrollArea, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtCore import Qt, QTimer

# ---------------------------
# Utility: formatted current time
# ---------------------------
def current_time_str():
    return datetime.datetime.now().strftime("%H:%M:%S")

# ---------------------------
# Printer Detail Dialog
# ---------------------------
class PrinterDetailDialog(QDialog):
    """Displays additional details for a printer."""
    def __init__(self, printer_data):
        super().__init__()
        self.setWindowTitle(f"Details for {printer_data['printer_id']}")
        self.resize(400, 300)
        layout = QVBoxLayout()
        # Display printer name and cumulative counts
        layout.addWidget(QLabel(f"Printer Name: {printer_data['printer_id']}"))
        printed = printer_data["pass_count"] + printer_data["fail_count"]
        layout.addWidget(QLabel(f"Total Printed: {printed}"))
        layout.addWidget(QLabel(f"Total Voided: {printer_data['fail_count']}"))
        if printed > 0:
            error_pct = f"{(printer_data['fail_count']/printed * 100):.1f}%"
        else:
            error_pct = "0%"
        layout.addWidget(QLabel(f"Quality Error %: {error_pct}"))
        layout.addWidget(QLabel(f"Last Update: {printer_data['last_event']}"))
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        self.setLayout(layout)

# ---------------------------
# Refined Dashboard / Live Monitor Widget
# ---------------------------
class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # Header with title and time interval selector
        header_layout = QHBoxLayout()
        header_label = QLabel("Dashboard / Live Monitor")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        self.interval_selector = QComboBox()
        # Options: Live, 1 hour, 4 hours, 8 hours
        self.interval_selector.addItems(["Live", "1 hour", "4 hours", "8 hours"])
        header_layout.addWidget(QLabel("Interval:"))
        header_layout.addWidget(self.interval_selector)
        main_layout.addLayout(header_layout)

        # Create the table for printer display.
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Printer", "Printed", "Voided", "Error %"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # Increase font size for readability
        font = QFont()
        font.setPointSize(11)
        self.table.setFont(font)
        # Stretch columns to fill available width
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Set default row height to better utilize space
        self.table.verticalHeader().setDefaultSectionSize(25)
        # Connect double-click to detail view
        self.table.cellDoubleClicked.connect(self.handle_row_click)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

        # Seed mock data for 15 printers
        self.all_printers = {}
        for i in range(1, 16):
            pid = f"p{str(i).zfill(2)}"
            self.all_printers[pid] = self.generate_mock_printer(pid)

        self.populate_table()

        # Timer to simulate data streaming updates every 2-5 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_table_data)
        self.reset_timer()

    def reset_timer(self):
        interval = random.randint(2000, 5000)  # interval in ms
        self.timer.start(interval)

    def generate_mock_printer(self, printer_id):
        # Generate mock values for pass_count and fail_count
        base_pass = 10 * random.randint(1, 5)
        return {
            "printer_id": printer_id,
            "pass_count": base_pass,
            "fail_count": random.randint(0, base_pass // 2),
            "last_event": current_time_str()
        }

    def populate_table(self):
        self.table.setRowCount(len(self.all_printers))
        for idx, pid in enumerate(sorted(self.all_printers.keys())):
            data = self.all_printers[pid]
            printed = data["pass_count"] + data["fail_count"]
            voided = data["fail_count"]
            error_pct = f"{(voided / printed * 100):.1f}%" if printed > 0 else "0%"
            self.table.setItem(idx, 0, QTableWidgetItem(pid))
            self.table.setItem(idx, 1, QTableWidgetItem(str(printed)))
            self.table.setItem(idx, 2, QTableWidgetItem(str(voided)))
            self.table.setItem(idx, 3, QTableWidgetItem(error_pct))

    def update_table_data(self):
        # Get selected interval; simulate multiplier for demonstration purposes
        interval = self.interval_selector.currentText()
        multiplier = {"Live": 1, "1 hour": 1, "4 hours": 2, "8 hours": 3}.get(interval, 1)
        for pid in self.all_printers:
            data = self.all_printers[pid]
            data["pass_count"] += random.randint(0, 5 * multiplier)
            data["fail_count"] += random.randint(0, 3 * multiplier)
            data["last_event"] = current_time_str()
        self.populate_table()
        self.reset_timer()

    def handle_row_click(self, row, column):
        # Retrieve the printer ID and show details when row is double-clicked
        pid_item = self.table.item(row, 0)
        if pid_item:
            pid = pid_item.text()
            printer_data = self.all_printers.get(pid)
            if printer_data:
                dlg = PrinterDetailDialog(printer_data)
                dlg.exec()

# ---------------------------
# Ticket / Job Entry
# ---------------------------
class TicketWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout()
        self.job_name = QLineEdit()
        self.product_code = QLineEdit()
        self.label_qty = QLineEdit()
        layout.addRow("Job Name:", self.job_name)
        layout.addRow("Product Code:", self.product_code)
        layout.addRow("Label Quantity:", self.label_qty)
        generate_btn = QPushButton("Generate Job")
        generate_btn.clicked.connect(self.generate_job)
        layout.addRow(generate_btn)
        self.setLayout(layout)

    def generate_job(self):
        if not self.job_name.text() or not self.product_code.text() or not self.label_qty.text().isdigit():
            QMessageBox.warning(self, "Validation Error", "Please enter valid job details.")
        else:
            QMessageBox.information(self, "Job Created", "Job successfully created (mock).")

# ---------------------------
# Database Generation
# ---------------------------
class DBGenerationWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout()
        self.start_serial = QLineEdit()
        self.quantity = QLineEdit()
        layout.addRow("Start Serial:", self.start_serial)
        layout.addRow("Quantity:", self.quantity)
        gen_btn = QPushButton("Generate DB")
        gen_btn.clicked.connect(self.generate_db)
        layout.addRow(gen_btn)
        self.setLayout(layout)

    def generate_db(self):
        if not self.start_serial.text().isdigit() or not self.quantity.text().isdigit():
            QMessageBox.warning(self, "Validation Error", "Enter numeric values only.")
        else:
            QMessageBox.information(self, "Success", "Database generated successfully (mock).")

# ---------------------------
# BarTender File Manager
# ---------------------------
class BarTenderWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout()
        self.template_path = QLineEdit()
        browse_template = QPushButton("Browse Template")
        browse_template.clicked.connect(self.browse_template)
        self.dest_path = QLineEdit()
        browse_dest = QPushButton("Browse Destination")
        browse_dest.clicked.connect(self.browse_dest)
        layout.addRow("Template File:", self.template_path)
        layout.addRow("", browse_template)
        layout.addRow("Destination Path:", self.dest_path)
        layout.addRow("", browse_dest)
        link_btn = QPushButton("Create/Link")
        link_btn.clicked.connect(self.link_file)
        layout.addRow(link_btn)
        self.setLayout(layout)

    def browse_template(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select .btw Template", "", "BarTender Files (*.btw)")
        if path:
            self.template_path.setText(path)

    def browse_dest(self):
        path = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if path:
            self.dest_path.setText(path)

    def link_file(self):
        QMessageBox.information(self, "Success", "BarTender file linked successfully (mock).")

# ---------------------------
# Test Print & Verification
# ---------------------------
class TestPrintWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        print_btn = QPushButton("Print 5 Labels")
        print_btn.clicked.connect(self.print_labels)
        layout.addWidget(print_btn)
        self.result_list = QListWidget()
        layout.addWidget(self.result_list)
        signoff_btn = QPushButton("Digital Sign-Off")
        signoff_btn.clicked.connect(self.sign_off)
        layout.addWidget(signoff_btn)
        self.setLayout(layout)

    def print_labels(self):
        self.result_list.clear()
        for i in range(5):
            self.result_list.addItem(f"Label {i+1}: EPC XYZ{100+i} - PASS")
        QMessageBox.information(self, "Test Print", "Test print completed (mock).")

    def sign_off(self):
        QMessageBox.information(self, "Sign-Off", "Test print verified and signed off (mock).")

# ---------------------------
# Roll Tracker
# ---------------------------
class RollTrackerWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Roll Tracker"))
        for roll in range(1, 3):
            bar = QProgressBar()
            bar.setValue(50)
            layout.addWidget(QLabel(f"Roll {roll}"))
            layout.addWidget(bar)
        pdf_btn = QPushButton("Print to PDF")
        pdf_btn.clicked.connect(lambda: QMessageBox.information(self, "Print", "Export to PDF (mock)."))
        layout.addWidget(pdf_btn)
        self.setLayout(layout)

# ---------------------------
# Reports & Logs
# ---------------------------
class ReportsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Job/Date:"))
        self.filter_input = QLineEdit()
        filter_layout.addWidget(self.filter_input)
        layout.addLayout(filter_layout)
        csv_btn = QPushButton("Download CSV")
        csv_btn.clicked.connect(lambda: QMessageBox.information(self, "Download", "CSV downloaded (mock)."))
        pdf_btn = QPushButton("Download PDF")
        pdf_btn.clicked.connect(lambda: QMessageBox.information(self, "Download", "PDF downloaded (mock)."))
        layout.addWidget(csv_btn)
        layout.addWidget(pdf_btn)
        self.setLayout(layout)

# ---------------------------
# Settings
# ---------------------------
class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        tabs = QTabWidget()
        file_tab = QWidget()
        file_layout = QFormLayout()
        file_layout.addRow("CSV File Path:", QLineEdit("Z:\\Path\\to\\csv_data.csv"))
        file_layout.addRow("Template Folder:", QLineEdit("Z:\\Path\\to\\templates"))
        file_tab.setLayout(file_layout)
        tabs.addTab(file_tab, "File Locations")
        printer_tab = QWidget()
        printer_layout = QVBoxLayout()
        printer_layout.addWidget(QLabel("Printer List (mock): p1, p2, …, p15"))
        printer_tab.setLayout(printer_layout)
        tabs.addTab(printer_tab, "Printers")
        roles_tab = QWidget()
        roles_layout = QVBoxLayout()
        roles_layout.addWidget(QLabel("User Roles (stubbed)"))
        roles_tab.setLayout(roles_layout)
        tabs.addTab(roles_tab, "User Roles")
        theme_btn = QPushButton("Toggle Dark/Light Theme")
        theme_btn.clicked.connect(lambda: QMessageBox.information(self, "Theme", "Theme toggled (mock)."))
        layout = QVBoxLayout()
        layout.addWidget(tabs)
        layout.addWidget(theme_btn)
        self.setLayout(layout)

# ---------------------------
# Main Navigation Shell
# ---------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RFID Workflow Management App Prototype")
        self.resize(1000, 700)
        toolbar = QToolBar("Main Navigation")
        
        # Make text and icons in toolbar slightly larger
        font = toolbar.font()
        font.setPointSize(font.pointSize() + 4)  # Increase font size by 2pt
        toolbar.setFont(font)

        self.addToolBar(toolbar)
        self.stack = QStackedWidget()
        self.widgets = {
            "Dashboard": DashboardWidget(),
            "Ticket": TicketWidget(),
            "DB Generation": DBGenerationWidget(),
            "BarTender": BarTenderWidget(),
            "Test Print": TestPrintWidget(),
            "Roll Tracker": RollTrackerWidget(),
            "Reports": ReportsWidget(),
            "Settings": SettingsWidget()
        }
        for name, widget in self.widgets.items():
            self.stack.addWidget(widget)
            action = QAction(name, self)
            action.triggered.connect(lambda checked, n=name: self.switch_module(n))
            toolbar.addAction(action)
        self.setCentralWidget(self.stack)
        self.switch_module("Dashboard")

    def switch_module(self, name):
        widget = self.widgets.get(name)
        if widget:
            index = self.stack.indexOf(widget)
            self.stack.setCurrentIndex(index)

# ---------------------------
# Run the Application
# ---------------------------
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
