from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIntValidator, QRegularExpressionValidator
from PyQt6.QtWidgets import QCompleter
from PyQt6.QtCore import Qt, QDate, QStringListModel, QRegularExpression

from jobdata import JobData
from serial_tracker import reserve_serials
from job_folder import create_job_folders
from util import load_settings

import os
SETTINGS_DATA = load_settings()


# The new Encoding Checklist Tab (full update!):
class EncodingChecklistTab(QWidget):
    FIELD_ORDER = [
        'customer','job_ticket','part_num','customer_po','item',
        'inlay_type','label_size','qty','overage','upc',
        'labels_per_roll','rolls'
    ]
    FIELD_LABELS = {
        'customer': "Customer",
        'job_ticket': "Job Ticket #",
        'part_num': "Part Num",
        'customer_po': "Customer PO",
        'item': "Item",
        'inlay_type': "Inlay Type",
        'label_size': "Label Size",
        'qty': "QTY",
        'overage': "Overage",
        'upc': "UPC",
        'labels_per_roll': "Labels Per Roll",
        'rolls': "Rolls (Auto Calc)",
    }
    def __init__(self, job: JobData):
        super().__init__()
        self.job = job
        self.layout = QVBoxLayout()
        self.form = QFormLayout()
        self.fields = {}

        # TEXT FIELDS
        text_fields = ['customer', 'job_ticket', 'part_num', 'customer_po', 'item']
        for key in text_fields:
            line = QLineEdit()
            line.setMaxLength(64)
            self.form.addRow(self.FIELD_LABELS[key], line)
            self.fields[key] = line

        # Inlay Type dropdown (dynamic)
        self.inlay_combo = QComboBox()
        self.inlay_combo.setEditable(True)
        self.inlay_combo.addItems(SETTINGS_DATA["inlay_types"])
        self.form.addRow(self.FIELD_LABELS['inlay_type'], self.inlay_combo)
        self.fields['inlay_type'] = self.inlay_combo

        # Label Size dropdown with autocomplete (dynamic)
        self.labelsize_combo = QComboBox()
        self.labelsize_combo.setEditable(True)
        self.completer = QCompleter(SETTINGS_DATA["label_sizes"])
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.labelsize_combo.setCompleter(self.completer)
        self.labelsize_combo.addItems(SETTINGS_DATA["label_sizes"])
        self.form.addRow(self.FIELD_LABELS['label_size'], self.labelsize_combo)
        self.fields['label_size'] = self.labelsize_combo

        combo_width = 160 
        self.inlay_combo.setFixedWidth(combo_width)
        self.labelsize_combo.setFixedWidth(combo_width)

        # QTY (numeric only, comma formatting)
        self.qty_field = QLineEdit()
        self.qty_field.setValidator(QIntValidator(0, 999999999))
        self.qty_field.setMaxLength(12)
        self.qty_field.textChanged.connect(lambda: self._format_commas_lineedit(self.qty_field))
        self.qty_field.textChanged.connect(self.auto_calc_rolls)
        self.form.addRow(self.FIELD_LABELS['qty'], self.qty_field)
        self.fields['qty'] = self.qty_field

        # Overage (allows numbers or %)
        self.overage_field = QLineEdit()
        re = QRegularExpression(r"^(\d+(,\d{3}){0,3}|(\d+%))?$")
        self.overage_field.setValidator(QRegularExpressionValidator(re))
        self.form.addRow(self.FIELD_LABELS['overage'], self.overage_field)
        self.fields['overage'] = self.overage_field

        # UPC (12 digits, numbers)
        self.upc_field = QLineEdit()
        self.upc_field.setMaxLength(12)
        re_upc = QRegularExpression(r"\d{0,12}")
        self.upc_field.setValidator(QRegularExpressionValidator(re_upc))
        self.form.addRow(self.FIELD_LABELS['upc'], self.upc_field)
        self.fields['upc'] = self.upc_field

        # Labels per roll / Rolls
        self.labels_per_roll_field = QLineEdit()
        self.labels_per_roll_field.setValidator(QIntValidator(1, 99999999))
        self.labels_per_roll_field.textChanged.connect(self.auto_calc_rolls)
        self.form.addRow(self.FIELD_LABELS['labels_per_roll'], self.labels_per_roll_field)
        self.fields['labels_per_roll'] = self.labels_per_roll_field

        self.rolls_label = QLabel("?")
        self.form.addRow(self.FIELD_LABELS['rolls'], self.rolls_label)
        self.fields['rolls'] = self.rolls_label

        # SERIAL LABEL (result display only)
        self.serial_label = QLabel("(Serials will be assigned when checklist is created)")
        self.form.addRow("Serials Reserved:", self.serial_label)

        # --- Create checklist button and checkbox ---
        self.make_db_chk = QCheckBox("Create folder and job database as well")
        self.make_db_chk.setChecked(True)
        self.create_btn = QPushButton("Create Checklist")
        self.create_btn.clicked.connect(self.handle_create_checklist)

        self.layout.addLayout(self.form)
        self.layout.addWidget(self.make_db_chk)
        self.layout.addWidget(self.create_btn)
        self.setLayout(self.layout)
        self.refresh()

    def _format_commas_lineedit(self, lineedit):
        txt = lineedit.text().replace(",", "")
        if not txt or not txt.isdigit():
            return
        val = int(txt)
        formatted = "{:,}".format(val)
        if lineedit.text() != formatted:
            lineedit.blockSignals(True)
            lineedit.setText(formatted)
            lineedit.blockSignals(False)

    def auto_calc_rolls(self):
        try:
            qty_val = int(self.qty_field.text().replace(",", ""))
            lbls = int(self.labels_per_roll_field.text().replace(",", ""))
            rolls = (qty_val + lbls - 1) // lbls if lbls > 0 else 0
            self.rolls_label.setText(str(rolls))
        except Exception:
            self.rolls_label.setText("?")

    def handle_create_checklist(self):
        # --- Validation rules ---
        # UPC: 12 digits, numeric
        upc = self.upc_field.text().strip()
        if len(upc) != 12 or not upc.isdigit():
            QMessageBox.warning(self, "UPC", "UPC must be exactly 12 digits (numeric only).")
            self.upc_field.setFocus()
            return
        # QTY check
        try:
            qty = int(self.qty_field.text().replace(",", "").strip())
        except Exception:
            QMessageBox.warning(self, "Missing", "Qty must be a number.")
            return
        # Overage check (accepts blank, number, or ##%)
        ov = self.overage_field.text().strip()
        if ov and not (ov.isdigit() or (ov.endswith("%") and ov[:-1].isdigit())):
            QMessageBox.warning(self, "Overage", "Overage must be blank, a number or percent (eg. 1000 or 10%).")
            self.overage_field.setFocus()
            return
        # Labels per roll check:
        if not self.labels_per_roll_field.text().replace(",", "").isdigit():
            QMessageBox.warning(self, "Labels Per Roll", "Labels Per Roll must be a number.")
            self.labels_per_roll_field.setFocus()
            return

        # All other fields
        values = {}
        for key in self.FIELD_ORDER:
            widget = self.fields.get(key)
            val = ""
            if isinstance(widget, QLineEdit):
                val = widget.text().strip()
            elif isinstance(widget, QComboBox):
                val = widget.currentText().strip()
            elif isinstance(widget, QLabel):
                val = widget.text().strip()
            values[key] = val

        # Get info for serial reserve and folder
        customer = values['customer']
        label_size = values['label_size']
        job_ticket = values['job_ticket']
        po = values['customer_po']
        date_str = QDate.currentDate().toString("yyyy-MM-dd")

        # SERIAL ALLOCATION (global tracker)
        start, stop = reserve_serials(job_ticket, customer, label_size, qty)
        self.serial_label.setText(f"{start:,} - {stop:,}")

        # Store in job/checklist_data
        self.job.checklist_data['serial_start'] = str(start)
        self.job.checklist_data['serial_stop'] = str(stop)

        # Folder/db: 
        if self.make_db_chk.isChecked():
            jdir = create_job_folders(customer, label_size, job_ticket, po, date_str)
            db_path = os.path.join(jdir, 'data', 'EPC_Database.xlsx')
            if not os.path.exists(db_path):
                try:
                    import pandas as pd
                    df = pd.DataFrame(columns=["EPC", "Serial", "UPC", "Date"])
                    df.to_excel(db_path, index=False)
                except Exception as ex:
                    QMessageBox.warning(
                        self, "Error", f"Unable to create database file:\n{ex}"
                    )
            QMessageBox.information(self, "Folders OK", f"Created dir:\n{jdir}")
        QMessageBox.information(self, "Serials Reserved", f"Serial range: {start} - {stop}")

        # Save main data fields
        for key in self.FIELD_ORDER:
            widget = self.fields.get(key)
            val = ""
            if isinstance(widget, QLineEdit):
                val = widget.text().strip()
            elif isinstance(widget, QComboBox):
                val = widget.currentText().strip()
            elif isinstance(widget, QLabel):
                val = widget.text().strip()
            self.job.checklist_data[key] = val

        self.job.checklist_data['start'] = str(start)
        self.job.checklist_data['stop'] = str(stop)

    def refresh(self):
        data = self.job.checklist_data
        # Set fields in UI (do this in PDF field order!)
        for key in self.FIELD_ORDER:
            val = data.get(key, "")
            widget = self.fields.get(key)
            if isinstance(widget, QLineEdit):
                widget.setText(str(val))
            elif isinstance(widget, QComboBox):
                idx = widget.findText(val)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
                else:
                    widget.setCurrentText(str(val))
            elif isinstance(widget, QLabel):
                widget.setText(str(val))