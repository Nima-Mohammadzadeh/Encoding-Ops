# workflow/encoding_checklist.py

import os
import tempfile
import shutil

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox, QDialog
)
from PyQt6.QtCore import QUrl, QTimer, Qt, QObject, pyqtSignal, QThread
from PyQt6.QtWebEngineWidgets import QWebEngineView

from data.jobdata import JobData
from util import load_settings

import time

SETTINGS_DATA = load_settings()

class ChecklistPDFWorker(QObject):
    finished = pyqtSignal(str)        # emits output path on success
    error = pyqtSignal(str, str)      # emits error message, traceback

    def __init__(self, job, outpath, template_path):
        super().__init__()
        self.job = job
        self.outpath = outpath
        self.template_path = template_path

    def run(self):
        try:
            self._fill_and_save_()
            self.finished.emit(self.outpath)
        except Exception as ex:
            import traceback
            self.error.emit(str(ex), traceback.format_exc())

    def _fill_and_save_pdf(self):
        import subprocess
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import NameObject

        checklist_dir = os.path.dirname(self.outpath)
        os.makedirs(checklist_dir, exist_ok=True)
        src = self.template_path
        dst = self.outpath
        reader = PdfReader(src)
        writer = PdfWriter()
        field_values = self.job.checklist_data.copy()
        fields = {k: str(field_values.get(k, "")) for k in reader.get_fields()}
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

        # Try flatten (optional, can remove if you don't need it)
        flattened = dst.replace(".pdf", "_flat.pdf")
        flattened_success = False
        try:
            subprocess.run(["qpdf", "--flatten-annotations=all", dst, flattened], check=True)
            os.replace(flattened, dst)
            flattened_success = True
        except FileNotFoundError:
            pass
        except Exception:
            pass
        if not flattened_success:
            try:
                subprocess.run(["pdftk", dst, "output", flattened, "flatten"], check=True)
                os.replace(flattened, dst)
            except FileNotFoundError:
                pass
            except Exception:
                pass

class EncodingChecklistTab(QWidget):
    PDF_TEMPLATE = r"Z:\3 Encoding and Printing Files\Checklists & Spreadsheets\Encoding Checklist V4.1.pdf"
    PDFJS_VIEWER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'pdfjs', 'viewer.html'))
    # ^--- Assumes [project]/static/pdfjs/viewer.html

    def __init__(self, job, jobs_modwidget=None):
        super().__init__()
        self.job = job
        self.jobs_modwidget = jobs_modwidget
        self.layout = QVBoxLayout(self)
        self._pdf_path = self._get_pdf_outpath()

        # PDF.js browser-based PDF preview
        self.web_pdf_view = QWebEngineView(self)
        self.layout.addWidget(self.web_pdf_view)

        self.btn_edit = QPushButton("Edit Checklist")
        self.btn_edit.clicked.connect(self._edit)
        hlayout = QHBoxLayout()
        hlayout.addStretch()
        hlayout.addWidget(self.btn_edit)
        self.layout.addLayout(hlayout)

        self.btn_ext = QPushButton("Open PDF in External Viewer")
        self.btn_ext.clicked.connect(self.open_external_pdf)
        self.layout.addWidget(self.btn_ext)

        QTimer.singleShot(0, self._init_pdf)

    def _init_pdf(self):
        if not os.path.exists(self._pdf_path):
            self._fill_and_save_pdf_async()
        else:
            self._show_pdf_in_browser()

    def _edit(self):
        if self.jobs_modwidget:
            self.jobs_modwidget.new_job_dialog(prefill=self.job.checklist_data)
            self._fill_and_save_pdf_async()

    def _get_pdf_outpath(self):
        checklist_dir = os.path.join(self.job.folder_path, 'Checklist')
        return os.path.join(checklist_dir, "checklist.pdf")

    def _fill_and_save_pdf_async(self):
        self._show_loading_placeholder("Generating checklist PDF, please wait...")

        self.pdf_thread = QThread(self)
        self.pdf_worker = ChecklistPDFWorker(self.job, self._pdf_path, self.PDF_TEMPLATE)
        self.pdf_worker.moveToThread(self.pdf_thread)
        self.pdf_thread.started.connect(self.pdf_worker.run)
        self.pdf_worker.finished.connect(self._on_pdf_filled)
        self.pdf_worker.finished.connect(self.pdf_thread.quit)
        self.pdf_worker.finished.connect(self.pdf_worker.deleteLater)
        self.pdf_thread.finished.connect(self.pdf_thread.deleteLater)
        self.pdf_worker.error.connect(self._on_worker_error)
        self.pdf_thread.start()

    def _on_pdf_filled(self, outpath):
        for _ in range(10):
            if os.path.exists(outpath) and os.path.getsize(outpath) > 0:
                break
            time.sleep(0.05)
        else:
            self._show_loading_placeholder(f"PDF not ready at {outpath}")
            return
        self._show_pdf_in_browser()

    def _on_worker_error(self, msg, tb):
        self._remove_loading_placeholder()
        QMessageBox.critical(
            self, "Checklist PDF Error",
            f"Failed to fill checklist PDF. Error:\n{msg}\n\nTraceback:\n{tb}"
        )

    def _show_loading_placeholder(self, msg="Loading..."):
        self.web_pdf_view.setHtml(
            f"<html><body><h2 style='color:gray;text-align:center'>{msg}</h2></body></html>"
        )

    def _remove_loading_placeholder(self):
        self.web_pdf_view.setHtml("<html><body></body></html>")

    def _show_pdf_in_browser(self):
        import shutil, tempfile, os
        from PyQt6.QtCore import QUrl

        # Point this to wherever you put web/viewer.html, UNC paths are OK!
        pdfjs_web_dir = r"Z:\pdfjs\web"
        viewer_html = os.path.join(pdfjs_web_dir, "viewer.html")

        if not os.path.exists(viewer_html):
            self.web_pdf_view.setHtml("<h3 style='color:red'>pdf.js <b>viewer.html</b> not found!</h3>")
            return

        # Copy the generated checklist PDF to a temp file for safe browser reading
        temp_pdf_path = os.path.join(tempfile.gettempdir(), "rfid_gui_tmp_checklist_preview.pdf")
        try:
            shutil.copy2(self._pdf_path, temp_pdf_path)
        except Exception as e:
            self._show_loading_placeholder(f"Could not preview PDF:<br>{e}")
            return

        # Compose viewer URL with PDF path in the ?file= param
        viewer_url = QUrl.fromLocalFile(viewer_html)
        pdf_url = QUrl.fromLocalFile(temp_pdf_path).toString()
        viewer_url.setQuery(f"file={pdf_url}")

        self.web_pdf_view.setUrl(viewer_url)

    def open_external_pdf(self):
        import sys, subprocess
        path = self._pdf_path
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open PDF:\n{e}")
