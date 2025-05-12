import sys
import random
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget

from ui.dashboard import DashboardWidget
from ui.jobs_module import JobsModuleWidget
from ui.reports import ReportsWidget
from ui.settings import SettingsWidget

from util import current_time_str


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RFID Workflow Management Suite")
        self.resize(1000, 700)
        # Printer data (mock, globally shared)
        self.printer_data = {}
        for i in range(1, 11):
            pid = f"p{str(i).zfill(2)}"
            base_pass = 10 * random.randint(1, 5)
            self.printer_data[pid] = {
                "printer_id": pid,
                "pass_count": base_pass,
                "fail_count": random.randint(0, base_pass // 2),
                "last_event": current_time_str()
            }
        tabs = QTabWidget()
        tabs.addTab(DashboardWidget(self.printer_data), "Dashboard")
        tabs.addTab(JobsModuleWidget(), "Jobs")
        tabs.addTab(ReportsWidget(), "Reports")
        tabs.addTab(SettingsWidget(self.printer_data), "Settings")
        self.setCentralWidget(tabs)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()