import sys
import os
import platform
import datetime as date
import xlwings as xw
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QMessageBox, QCheckBox, QFileDialog
)


class ExcelForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Excel Checklist Filler (xlwings)")

        self.excel_path: str | None = None

        # ── Layouts ────────────────────────────────────────────
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()

        # ── File‑chooser button ────────────────────────────────
        self.browse_btn = QPushButton("Browse for Excel Checklist…")
        self.browse_btn.clicked.connect(self.select_excel_file)
        main_layout.addWidget(self.browse_btn)

        # ── Text fields ────────────────────────────────────────
        self.customer       = QLineEdit()
        self.part_num       = QLineEdit()
        self.job_ticket_num = QLineEdit()
        self.customer_po    = QLineEdit()
        self.inlay_type     = QLineEdit()
        self.label_size     = QLineEdit()
        self.layout_field   = QLineEdit()
        self.qty            = QLineEdit()
        self.Start          = QLineEdit()
        self.Stop           = QLineEdit()
        self.LPR            = QLineEdit()
        self.ROLLS          = QLineEdit()
        self.UPC            = QLineEdit()
        self.Item           = QLineEdit()
        
        
        

        form_layout.addRow("Customer:",        self.customer)
        form_layout.addRow("Part #:",          self.part_num)
        form_layout.addRow("Job Ticket #:",    self.job_ticket_num)
        form_layout.addRow("Customer PO #:",   self.customer_po)
        form_layout.addRow("Inlay Type:",      self.inlay_type)
        form_layout.addRow("Label Size:",      self.label_size)
        form_layout.addRow("Layout:",          self.layout_field)
        form_layout.addRow("Start:",           self.Start)
        form_layout.addRow("Stop:",            self.Stop)
        form_layout.addRow("LPR:",             self.LPR)
        form_layout.addRow("ROLLS:",           self.ROLLS)
        form_layout.addRow("UPC:",             self.UPC)
        form_layout.addRow("Item:",            self.Item)

        # ── Checkbox example ──────────────────────────────────
        self.verify_customer_cb = QCheckBox("Verify customer name?")
        form_layout.addRow(self.verify_customer_cb)

        main_layout.addLayout(form_layout)

        # ── Generate button ───────────────────────────────────
        gen_btn = QPushButton("Generate Filled Checklist")
        gen_btn.clicked.connect(self.generate_excel)
        main_layout.addWidget(gen_btn)

        self.setLayout(main_layout)

    # ──────────────────────────────────────────────────────────
    #  Select template
    # ──────────────────────────────────────────────────────────
    def select_excel_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel Template", "", "Excel files (*.xlsx)"
        )
        if path:
            self.excel_path = path
            self.browse_btn.setText(f"Selected: {os.path.basename(path)}")

    # ──────────────────────────────────────────────────────────
    #  Generate filled file with xlwings
    # ──────────────────────────────────────────────────────────
    def generate_excel(self):
        now = date.datetime.now()
        if not self.excel_path:
            QMessageBox.warning(self, "No file chosen", "Please select an Excel checklist first.")
            return

        try:
            # macOS must show Excel; Windows can hide if desired.
            visible = platform.system() != "Darwin"
            app = xw.App(visible=visible)
            wb  = app.books.open(self.excel_path)
            sht = wb.sheets[0]  # first sheet; change if needed

            # ── Write text fields ─────────────────────────────
            sht["M1"].value = now
            
            sht["C2"].value = self.customer.text()
            sht["C3"].value = self.part_num.text()
            sht["C4"].value = self.job_ticket_num.text()
            sht["D5"].value = self.customer_po.text()
            sht["C6"].value = self.inlay_type.text()
            sht["C7"].value = self.label_size.text()
            sht["C8"].value = self.layout_field.text()
            sht["B9"].value = self.qty.text()
            sht["J2"].value = self.Start.text()
            sht["J3"].value = self.Stop.text()
            sht["I4"].value = self.LPR.text()
            sht["I5"].value = self.UPC.text()
            sht["I6"].value = self.Item.text()
            sht["J3"].value = self.Stop.text()

            # ── Checkbox logic (✓ or X) ──────────────────────
            sht["A12"].value = "✓" if self.verify_customer_cb.isChecked() else "X"

            # ── Save copy next to original ───────────────────
            base, ext = os.path.splitext(self.excel_path)
            out_path  = f"{base}_Filled{ext}"
            wb.save(out_path)
            wb.close()
            app.quit()

            QMessageBox.information(
                self, "Success", f"Checklist filled and saved:\n{out_path}"
            )
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Something went wrong:\n{exc}")


# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = ExcelForm()
    gui.show()
    sys.exit(app.exec())
