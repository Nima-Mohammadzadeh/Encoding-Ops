# pdf_form_filler.py
#
# Requires:  pip install PyQt6 pypdf
# (Qt ≥ 6.4 is fine; pypdf ≥ 4.0 recommended)

import sys
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate

from pypdf import PdfReader, PdfWriter


FIELD_NAMES = [
    "customer", "part_num", "job_ticket", "customer_po", "inlay_type",
    "label_size", "layout", "qty", "start", "stop", "lpr", "rolls",
    "upc", "item", "Date", "Production_qty", "Label_type", "overage"
]


class PDFFormFiller(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Form‑Filler")

        self.pdf_path: Path | None = None

        # ── Layout skeleton ──────────────────────────────────────────
        root = QVBoxLayout(self)
        pick_row = QHBoxLayout()
        form = QFormLayout()
        btn_row = QHBoxLayout()
        root.addLayout(pick_row)
        root.addLayout(form)
        root.addStretch()
        root.addLayout(btn_row)

        # ── “Choose PDF” row ────────────────────────────────────────
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        pick_btn = QPushButton("Select PDF…")
        pick_btn.clicked.connect(self.choose_pdf)

        pick_row.addWidget(self.path_edit)
        pick_row.addWidget(pick_btn)

        # ── dynamic field widgets ───────────────────────────────────
        self.inputs: dict[str, QLineEdit] = {}
        for name in FIELD_NAMES:
            if name.lower() == "date":
                widget = QDateEdit()
                widget.setCalendarPopup(True)
                widget.setDate(QDate.currentDate())
            else:
                widget = QLineEdit()
            self.inputs[name] = widget
            form.addRow(name, widget)

        # ── bottom buttons ──────────────────────────────────────────
        fill_btn = QPushButton("Fill && Save")
        fill_btn.clicked.connect(self.fill_pdf)
        quit_btn = QPushButton("Quit")
        quit_btn.clicked.connect(self.close)

        btn_row.addStretch()
        btn_row.addWidget(fill_btn)
        btn_row.addWidget(quit_btn)

    # ────────────────────────────────────────────────────────────────
    def choose_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose PDF template", "", "PDF files (*.pdf)")
        if path:
            self.pdf_path = Path(path)
            self.path_edit.setText(str(self.pdf_path))

    # ────────────────────────────────────────────────────────────────
    def fill_pdf(self):
        if not self.pdf_path:
            QMessageBox.warning(self, "No PDF chosen",
                                "Please select a PDF template first.")
            return

        # collect values
        data = { fname: 
                 (self.inputs[fname].date().toString("yyyy‑MM‑dd")
                  if isinstance(self.inputs[fname], QDateEdit)
                  else self.inputs[fname].text())
                 for fname in FIELD_NAMES }

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save filled PDF",
            str(self.pdf_path.stem) + "_filled.pdf",
            "PDF files (*.pdf)")
        if not save_path:
            return

        try:
            reader = PdfReader(str(self.pdf_path))
            # DEBUGGING: uncomment to confirm fields exist
            # print("Fields:", reader.get_fields())
            # print("AcroForm:", reader.trailer["/Root"].get("/AcroForm"))

            writer = PdfWriter()
            writer.append_pages_from_reader(reader)

            # Copy over the form catalog
            from pypdf.generic import NameObject
            acro = reader.trailer["/Root"].get("/AcroForm")
            if acro:
                writer._root_object.update({ NameObject("/AcroForm"): acro })

            writer.update_page_form_field_values(writer.pages[0], data)
            writer.set_need_appearances_writer()

            with open(save_path, "wb") as f:
                writer.write(f)

            QMessageBox.information(
                self, "Success", f"Saved filled PDF to:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"Failed to fill PDF:\n{e}")

# ── main entry‑point ───────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = PDFFormFiller()
    w.resize(420, 600)
    w.show()
    sys.exit(app.exec())
