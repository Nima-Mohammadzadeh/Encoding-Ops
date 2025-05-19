# ===== settings.py =====

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QTime

from util import load_settings, save_settings, current_time_str,load_shift_settings, save_shift_settings
SETTINGS_DATA = load_settings()


class ShiftSettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = load_shift_settings()
        layout = QFormLayout()
        self.day_start = QTimeEdit()
        self.day_start.setTime(QTime.fromString(self.settings['day']['start'], "HH:mm"))
        self.day_end = QTimeEdit()
        self.day_end.setTime(QTime.fromString(self.settings['day']['end'], "HH:mm"))
        self.night_start = QTimeEdit()
        self.night_start.setTime(QTime.fromString(self.settings['night']['start'], "HH:mm"))
        self.night_end = QTimeEdit()
        self.night_end.setTime(QTime.fromString(self.settings['night']['end'], "HH:mm"))
        layout.addRow("Day Shift Start:", self.day_start)
        layout.addRow("Day Shift End:", self.day_end)
        layout.addRow("Night Shift Start:", self.night_start)
        layout.addRow("Night Shift End:", self.night_end)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        layout.addRow(save_btn)
        self.setLayout(layout)

    def save(self):
        self.settings['day']['start'] = self.day_start.time().toString("HH:mm")
        self.settings['day']['end'] = self.day_end.time().toString("HH:mm")
        self.settings['night']['start'] = self.night_start.time().toString("HH:mm")
        self.settings['night']['end'] = self.night_end.time().toString("HH:mm")
        save_shift_settings(self.settings)
        QMessageBox.information(self, "Saved", "Shift settings updated.")




class PrinterSettingsWidget(QWidget):
    def __init__(self, printer_data):
        super().__init__()
        self.printer_data = printer_data
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["Printer Name"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked |
                                    QTableWidget.EditTrigger.SelectedClicked)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        add_layout = QHBoxLayout()
        self.new_printer_edit = QLineEdit()
        self.new_printer_edit.setPlaceholderText("New printer name")
        add_layout.addWidget(self.new_printer_edit)
        add_btn = QPushButton("Add Printer")
        add_btn.clicked.connect(self.add_printer)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)
        del_btn = QPushButton("Delete Selected")
        del_btn.clicked.connect(self.delete_selected)
        layout.addWidget(del_btn)
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)
        layout.addWidget(save_btn)
        self.setLayout(layout)
        self.populate_table()
    def populate_table(self):
        printers = sorted(self.printer_data.keys())
        self.table.setRowCount(len(printers))
        for idx, pid in enumerate(printers):
            item = QTableWidgetItem(pid)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(idx, 0, item)
    def add_printer(self):
        name = self.new_printer_edit.text().strip()
        if name:
            if name in self.printer_data:
                QMessageBox.warning(self, "Duplicate", "Printer already exists.")
            else:
                self.printer_data[name] = {"printer_id": name,
                                           "pass_count": 0,
                                           "fail_count": 0,
                                           "last_event": current_time_str()}
                self.populate_table()
                self.new_printer_edit.clear()
    def delete_selected(self):
        selected = self.table.selectedItems()
        if selected:
            for item in selected:
                pid = item.text()
                if pid in self.printer_data:
                    del self.printer_data[pid]
            self.populate_table()
    def save_changes(self):
        new_data = {}
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                new_name = item.text().strip()
                if new_name:
                    if new_name in self.printer_data:
                        new_data[new_name] = self.printer_data[new_name]
                    else:
                        new_data[new_name] = {"printer_id": new_name,
                                              "pass_count": 0,
                                              "fail_count": 0,
                                              "last_event": current_time_str()}
        self.printer_data.clear()
        self.printer_data.update(new_data)
        QMessageBox.information(self, "Saved", "Printer settings updated.")

class InlayTypeSettingsWidget(QWidget):
    def __init__(self, settings_data):
        super().__init__()
        self.settings_data = settings_data
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.refresh_list()
        layout.addWidget(QLabel("Inlay Types:"))
        layout.addWidget(self.list_widget)
        edit_layout = QHBoxLayout()
        self.new_input = QLineEdit()
        edit_layout.addWidget(self.new_input)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_item)
        edit_layout.addWidget(add_btn)
        layout.addLayout(edit_layout)
        edit_rename_layout = QHBoxLayout()
        self.rename_input = QLineEdit()
        edit_rename_layout.addWidget(self.rename_input)
        rename_btn = QPushButton("Rename")
        rename_btn.clicked.connect(self.rename_item)
        edit_rename_layout.addWidget(rename_btn)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_selected)
        edit_rename_layout.addWidget(del_btn)
        layout.addLayout(edit_rename_layout)
        self.setLayout(layout)
        self.list_widget.currentRowChanged.connect(self.select_item)
    def refresh_list(self):
        self.list_widget.clear()
        self.list_widget.addItems(self.settings_data["inlay_types"])
    def add_item(self):
        name = self.new_input.text().strip()
        if name and name not in self.settings_data["inlay_types"]:
            self.settings_data["inlay_types"].append(name)
            save_settings(self.settings_data)
            self.refresh_list()
            self.new_input.clear()
    def delete_selected(self):
        idx = self.list_widget.currentRow()
        if idx >= 0:
            del self.settings_data["inlay_types"][idx]
            save_settings(self.settings_data)
            self.refresh_list()
    def rename_item(self):
        idx = self.list_widget.currentRow()
        new_name = self.rename_input.text().strip()
        if idx >= 0 and new_name:
            self.settings_data["inlay_types"][idx] = new_name
            save_settings(self.settings_data)
            self.refresh_list()
            self.rename_input.clear()
    def select_item(self, row):
        if row >= 0:
            self.rename_input.setText(self.settings_data["inlay_types"][row])
        else:
            self.rename_input.clear()


class LabelSizeSettingsWidget(QWidget):
    def __init__(self, settings_data):
        super().__init__()
        self.settings_data = settings_data
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.refresh_list()
        layout.addWidget(QLabel("Label Sizes:"))
        layout.addWidget(self.list_widget)
        edit_layout = QHBoxLayout()
        self.new_input = QLineEdit()
        edit_layout.addWidget(self.new_input)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_item)
        edit_layout.addWidget(add_btn)
        layout.addLayout(edit_layout)
        edit_rename_layout = QHBoxLayout()
        self.rename_input = QLineEdit()
        edit_rename_layout.addWidget(self.rename_input)
        rename_btn = QPushButton("Rename")
        rename_btn.clicked.connect(self.rename_item)
        edit_rename_layout.addWidget(rename_btn)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_selected)
        edit_rename_layout.addWidget(del_btn)
        layout.addLayout(edit_rename_layout)
        self.setLayout(layout)
        self.list_widget.currentRowChanged.connect(self.select_item)
    def refresh_list(self):
        self.list_widget.clear()
        self.list_widget.addItems(self.settings_data["label_sizes"])
    def add_item(self):
        name = self.new_input.text().strip()
        if name and name not in self.settings_data["label_sizes"]:
            self.settings_data["label_sizes"].append(name)
            save_settings(self.settings_data)
            self.refresh_list()
            self.new_input.clear()
    def delete_selected(self):
        idx = self.list_widget.currentRow()
        if idx >= 0:
            del self.settings_data["label_sizes"][idx]
            save_settings(self.settings_data)
            self.refresh_list()
    def rename_item(self):
        idx = self.list_widget.currentRow()
        new_name = self.rename_input.text().strip()
        if idx >= 0 and new_name:
            self.settings_data["label_sizes"][idx] = new_name
            save_settings(self.settings_data)
            self.refresh_list()
            self.rename_input.clear()
    def select_item(self, row):
        if row >= 0:
            self.rename_input.setText(self.settings_data["label_sizes"][row])
        else:
            self.rename_input.clear()

class SettingsWidget(QWidget):
    def __init__(self, printer_data):
        super().__init__()
        tabs = QTabWidget()
        # File locations (stub)
        file_tab = QWidget()
        file_layout = QFormLayout()
        file_layout.addRow("CSV File Path:", QLineEdit("Z:\\Path\\to\\csv_data.csv"))
        file_layout.addRow("Template Folder:", QLineEdit("Z:\\Path\\to\\templates"))
        file_tab.setLayout(file_layout)
        tabs.addTab(file_tab, "File Locations")
        # Printer management tab
        printer_tab = PrinterSettingsWidget(printer_data)
        tabs.addTab(printer_tab, "Printers")
        # Inlay & label management
        inlay_tab = InlayTypeSettingsWidget(SETTINGS_DATA)
        labelsize_tab = LabelSizeSettingsWidget(SETTINGS_DATA)
        tabs.addTab(inlay_tab, "Inlay Types")
        tabs.addTab(labelsize_tab, "Label Sizes")
        
        shift_tab = ShiftSettingsWidget()   # <-- ADD THIS LINE
        tabs.addTab(shift_tab, "Shift Settings")
        
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


