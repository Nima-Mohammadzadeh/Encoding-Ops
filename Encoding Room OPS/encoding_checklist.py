#Encoding_checklist.py
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIntValidator, QRegularExpressionValidator
from PyQt6.QtWidgets import QCompleter
from PyQt6.QtCore import Qt, QDate, QStringListModel, QRegularExpression

from jobdata import JobData
from serial_tracker import reserve_serials
from job_folder import create_job_folders
from util import load_settings

from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtPdf import QPdfDocument


from pypdf import PdfReader, PdfWriter

import os
SETTINGS_DATA = load_settings()

class EncodingChecklistTab(QWidget):
    # --- PDF template assumed at project root (template.pdf) ---
    PDF_TEMPLATE = r"Z:\3 Encoding and Printing Files\Checklists & Spreadsheets\Encoding Checklist V4.1.pdf"

    def __init__(self, job, jobs_modwidget=None):
        super().__init__()
        self.job = job
        self.jobs_modwidget = jobs_modwidget   # to call back for 'edit'
        self.layout = QVBoxLayout()
        self._pdf_path = self._get_pdf_outpath()
        self.pdf_widget = QPdfView(self)
        self.btn_edit = QPushButton("Edit Checklist")
        self.btn_edit.clicked.connect(self._edit)

        self.layout.addWidget(self.pdf_widget)
        hlayout = QHBoxLayout()
        hlayout.addStretch()
        hlayout.addWidget(self.btn_edit)
        self.layout.addLayout(hlayout)
        self.setLayout(self.layout)

        if not os.path.exists(self._pdf_path):
            # No checklist yet, so create it
            self._fill_and_save_pdf()

        self._load_pdf_viewer()

    def _edit(self):
        # Re-open wizard (prefilled), update, refill pdf, reload view
        if self.jobs_modwidget: # Use outer widget's dialog for consistency
            self.jobs_modwidget.new_job_dialog(prefill=self.job.checklist_data)
            # Here, after dialog the self.job.checklist_data may be updated
            self._fill_and_save_pdf()
            self._load_pdf_viewer()

    def _get_pdf_outpath(self):
        # Checklist PDF lives in job's Checklist subfolder
        checklist_dir = os.path.join(self.job.folder_path, 'Checklist')
        os.makedirs(checklist_dir, exist_ok=True)
        return os.path.join(checklist_dir, "checklist.pdf")

    def _fill_and_save_pdf(self):
        import subprocess
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import NameObject

        src = self.PDF_TEMPLATE
        dst = self._pdf_path
        reader = PdfReader(src)
        writer = PdfWriter()
        field_values = self.job.checklist_data.copy()

        # Print for debug: You can comment this out
        print("Checklist fields to fill:")
        for k in reader.get_fields():
            print(f"{k}: {field_values.get(k, '')}")

        fields = {k: str(field_values.get(k,'')) for k in reader.get_fields()}

        writer.append_pages_from_reader(reader)
        if "/AcroForm" in reader.trailer["/Root"]:
            writer._root_object.update({
                NameObject("/AcroForm"): reader.trailer["/Root"]["/AcroForm"]
            })
        else:
            raise RuntimeError("Template is missing /AcroForm! Cannot fill form.")
        writer.update_page_form_field_values(writer.pages[0], fields)
        with open(dst, "wb") as outf:
            writer.write(outf)

        # Try qpdf flattening first, then pdftk, else fallback
        flattened = dst.replace(".pdf", "_flat.pdf")
        flattened_success = False
        flatten_tool_used = ""

        # Try qpdf flattening (preferred, more modern)
        try:
            result = subprocess.run(["qpdf", "--flatten-annotations=all", dst, flattened], check=True)
            os.replace(flattened, dst)
            flattened_success = True
            flatten_tool_used = "qpdf"
        except FileNotFoundError:
            pass  # qpdf not available, will try pdftk
        except Exception as ex:
            print("qpdf flatten failed:", ex)

        # Try pdftk as fallback
        if not flattened_success:
            try:
                result = subprocess.run(
                    ["pdftk", dst, "output", flattened, "flatten"], check=True
                )
                os.replace(flattened, dst)
                flattened_success = True
                flatten_tool_used = "pdftk"
            except FileNotFoundError:
                pass  # pdftk not available
            except Exception as ex:
                print("pdftk flatten failed:", ex)

        # FINAL check
        if not flattened_success:
            QMessageBox.warning(self, "PDF Flattening Disabled",
                "WARNING: Neither qpdf nor pdftk found. The checklist PDF will NOT be properly flattened, "
                "and may appear blank in this app.\n\n"
                "To fix: install qpdf (https://sourceforge.net/projects/qpdf/) or pdftk (https://www.pdflabs.com/tools/pdftk-server/) "
                "and add it to your PATH, then restart this program.")
        else:
            print(f"Checklist successfully flattened with {flatten_tool_used}.")


    def _load_pdf_viewer(self):
        import time
        time.sleep(0.1)  # thoroughly ensure flush; remove for SSDs if fast enough
        doc = QPdfDocument(self)
        status = doc.load(self._pdf_path)
        if status != QPdfDocument.Status.Ready:
            QMessageBox.warning(self, "PDF error", f"Failed to load checklist PDF at {self._pdf_path}")
        self.pdf_widget.setDocument(None)
        self.pdf_widget.setDocument(doc)
