# encoding_checklist.py

from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIntValidator, QRegularExpressionValidator
from PyQt6.QtWidgets import QCompleter
from PyQt6.QtCore import Qt, QDate, QStringListModel, QRegularExpression, QObject, pyqtSignal, QThread
from PyQt6.QtCore import QTimer


from data.jobdata import JobData
from data.serial_tracker import reserve_serials
from util import load_settings

from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtPdf import QPdfDocument

import os

SETTINGS_DATA = load_settings()

class PDFLoadWorker(QObject):
    finished = pyqtSignal(str)   # int = QPdfDocument.Status
    error = pyqtSignal(str)

    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path

    def run(self):
        import os
        # Optionally, you could do open(self.pdf_path, 'rb').read() etc.
        if not os.path.exists(self.pdf_path):
            self.error.emit(f"File not found: {self.pdf_path}")
            return
        # Optionally, can check if file can be opened/read etc.
        self.finished.emit(self.pdf_path)


### WORKER (keep only one copy!)
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
            self._fill_and_save_pdf()
            self.finished.emit(self.outpath)
        except Exception as ex:
            import traceback
            self.error.emit(str(ex), traceback.format_exc())
    
    def _fill_and_save_pdf(self):
        import os
        checklist_dir = os.path.dirname(self.outpath)
        os.makedirs(checklist_dir, exist_ok=True)  # Now happening in worker threads
        import subprocess
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import NameObject

        src = self.template_path
        dst = self.outpath
        reader = PdfReader(src)
        writer = PdfWriter()
        field_values = self.job.checklist_data.copy()
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

        # Try qpdf flattening
        flattened = dst.replace(".pdf", "_flat.pdf")
        flattened_success = False
        try:
            result = subprocess.run(["qpdf", "--flatten-annotations=all", dst, flattened], check=True)
            os.replace(flattened, dst)
            flattened_success = True
        except FileNotFoundError:
            pass
        except Exception as ex:
            pass
        if not flattened_success:
            try:
                result = subprocess.run(
                    ["pdftk", dst, "output", flattened, "flatten"], check=True
                )
                os.replace(flattened, dst)
                flattened_success = True
            except FileNotFoundError:
                pass
            except Exception as ex:
                pass

class EncodingChecklistTab(QWidget):
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

        '''if not os.path.exists(self._pdf_path):
            self._fill_and_save_pdf_async()
        else:
            self._load_pdf_viewer()
            '''
        QTimer.singleShot(0, self._init_pdf)
        
    def _init_pdf(self):
        if not os.path.exists(self._pdf_path):
            self._fill_and_save_pdf_async()
        else:
            self._load_pdf_viewer()
        

    def _edit(self):
        if self.jobs_modwidget:  # Use outer widget's dialog for consistency
            self.jobs_modwidget.new_job_dialog(prefill=self.job.checklist_data)
            self._fill_and_save_pdf_async()  # Use async version!

    def _get_pdf_outpath(self):
        checklist_dir = os.path.join(self.job.folder_path, 'Checklist')
        return os.path.join(checklist_dir, "checklist.pdf")

    def _fill_and_save_pdf_async(self):
        self.progress = QProgressDialog("Filling checklist PDF...", None, 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress.setAutoClose(False)
        self.progress.setAutoReset(False)
        self.progress.show()

        self.pdf_thread = QThread(self)
        self.pdf_worker = ChecklistPDFWorker(
            self.job, self._pdf_path, self.PDF_TEMPLATE)
        self.pdf_worker.moveToThread(self.pdf_thread)
        self.pdf_thread.started.connect(self.pdf_worker.run)
        self.pdf_worker.finished.connect(self._on_pdf_filled)
        self.pdf_worker.finished.connect(self.pdf_thread.quit)
        self.pdf_worker.finished.connect(self.pdf_worker.deleteLater)
        self.pdf_thread.finished.connect(self.pdf_thread.deleteLater)
        self.pdf_worker.error.connect(self._on_worker_error)
        self.pdf_thread.start()

    def _on_pdf_filled(self, outpath):
        self.progress.close()
        self._load_pdf_viewer()

    def _on_worker_error(self, msg, tb):
        self.progress.close()
        QMessageBox.critical(
            self, "Checklist PDF Error",
            f"Failed to fill checklist PDF. Error:\n{msg}\n\nTraceback:\n{tb}"
        )

    def _load_pdf_viewer(self):
        self.progress = QProgressDialog("Loading checklist PDF...", None, 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress.setAutoClose(False)
        self.progress.setAutoReset(False)
        self.progress.show()
        self.pdfload_thread = QThread(self)
        self.pdfload_worker = PDFLoadWorker(self._pdf_path)
        self.pdfload_worker.moveToThread(self.pdfload_thread)
        self.pdfload_thread.started.connect(self.pdfload_worker.run)
        self.pdfload_worker.finished.connect(self._on_load_success)
        self.pdfload_worker.finished.connect(self.pdfload_thread.quit)
        self.pdfload_worker.finished.connect(self.pdfload_worker.deleteLater)
        self.pdfload_thread.finished.connect(self.pdfload_thread.deleteLater)
        self.pdfload_worker.error.connect(self._on_load_error)
        self.pdfload_thread.start()

    def _on_load_success(self, path):
        self.progress.close()
        doc = QPdfDocument(self)   # Only create in GUI thread!
        status = doc.load(path)
        if status == QPdfDocument.Status.Error:
            QMessageBox.warning(self, "PDF error", f"Failed to load checklist PDF at:\n{path}\n\nStatus code: {status}")
            return
        self.pdf_widget.setDocument(doc)

    def _on_load_error(self, msg):
        self.progress.close()
        QMessageBox.warning(self, "PDF error", msg)
