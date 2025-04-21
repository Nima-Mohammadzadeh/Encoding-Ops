#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, messagebox, BooleanVar, ttk
import traceback
import os, sys
from pathlib import Path
from math import ceil
from datetime import date
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject, TextStringObject

# Constants for grouping
DETAIL_KEYS = {'customer','part_num','job_ticket','customer_po','inlay_type','label_size','layout','start','stop','upc','item'}
CONFIG_KEYS = {'qty','lpr','rolls','overage','production_qty','label_type'}

# Label type previews
LABEL_PREVIEWS = {
    "Type A": "previews/type_a.png",
    "Type B": "previews/type_b.png",
    "Type C": "previews/type_c.png",
}

class DynamicPDFFormFiller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Form Filler")
        self.geometry("700x700")
        self.pdf_path = tk.StringVar()
        self.field_vars = {}    # normalized_key -> tk.Variable
        self.pdf_map    = {}    # normalized_key -> actual PDF field name
        self.preview_photo = None
        self.row = {'details':0,'config':0,'checks':0,'misc':0}

        # File picker
        picker = tk.Frame(self)
        picker.pack(fill="x", padx=10, pady=(10,0))
        tk.Label(picker, text="Template PDF:").pack(side="left")
        tk.Entry(picker, textvariable=self.pdf_path).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(picker, text="Browse…", command=self.browse_pdf).pack(side="right")

        # Notebook for sections
        self.notebook = ttk.Notebook(self)
        self.frame_details = ttk.Frame(self.notebook)
        self.frame_config  = ttk.Frame(self.notebook)
        self.frame_checks  = ttk.Frame(self.notebook)
        self.frame_misc    = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_details, text="Details")
        self.notebook.add(self.frame_config,  text="Config")
        self.notebook.add(self.frame_checks,  text="Approvals")
        self.notebook.add(self.frame_misc,    text="Misc")
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Save button
        self.save_btn = tk.Button(self, text="Save & Fill PDF", command=self.save_filled)
        self.save_btn.pack(pady=(0,10))

    def browse_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF","*.pdf")])
        if not path:
            return
        self.pdf_path.set(path)
        self.load_fields(path)

    def load_fields(self, path):
        # clear previous
        for frame in (self.frame_details, self.frame_config, self.frame_checks, self.frame_misc):
            for w in frame.winfo_children():
                w.destroy()
        self.field_vars.clear()
        self.pdf_map.clear()
        for k in self.row:
            self.row[k] = 0

        reader = PdfReader(path)
        fields = reader.get_fields() or {}
        if not fields:
            messagebox.showerror("No Fields",
                "PDF has no form fields. Export with 'Create PDF form'.")
            return

        for name, info in fields.items():
            norm = name.lower()
            ftype = info.get("/FT")
            # select frame & group
            if norm in DETAIL_KEYS:
                frame, grp = self.frame_details, 'details'
            elif norm in CONFIG_KEYS:
                frame, grp = self.frame_config, 'config'
            elif ftype == "/Btn":
                frame, grp = self.frame_checks, 'checks'
            else:
                frame, grp = self.frame_misc,   'misc'
            r = self.row[grp]

            # label
            lbl = tk.Label(frame, text=name)
            lbl.grid(row=r, column=0, sticky='w', padx=5, pady=3)

            # variable & widget
            if norm == 'qty':
                var = tk.IntVar(value=0)
                ent = tk.Entry(frame, textvariable=var)
                ent.grid(row=r, column=1, sticky='ew', padx=5)
                var.trace_add('write', lambda *a: self._recalc())

            elif norm == 'lpr':
                var = tk.IntVar(value=1)
                ent = tk.Entry(frame, textvariable=var)
                ent.grid(row=r, column=1, sticky='ew', padx=5)
                var.trace_add('write', lambda *a: self._recalc())

            elif norm == 'rolls':
                var = tk.IntVar(value=0)
                ent = tk.Entry(frame, textvariable=var, state='readonly')
                ent.grid(row=r, column=1, sticky='ew', padx=5)

            elif norm == 'overage':
                var = tk.DoubleVar(value=0.0)
                sb = tk.Spinbox(frame, from_=0, to=100, textvariable=var, width=5)
                sb.grid(row=r, column=1, sticky='w', padx=5)
                tk.Label(frame, text="%").grid(row=r, column=2, sticky='w')
                var.trace_add('write', lambda *a: self._recalc())

            elif norm == 'production_qty':
                var = tk.IntVar(value=0)
                ent = tk.Entry(frame, textvariable=var, state='readonly')
                ent.grid(row=r, column=1, sticky='ew', padx=5)

            elif norm == 'date':
                var = tk.StringVar(value=date.today().isoformat())
                ent = tk.Entry(frame, textvariable=var, state='readonly')
                ent.grid(row=r, column=1, sticky='ew', padx=5)

            elif norm == 'label_type':
                var = tk.StringVar(value=list(LABEL_PREVIEWS.keys())[0])
                om = tk.OptionMenu(frame, var, *LABEL_PREVIEWS.keys(), command=self._update_preview)
                om.grid(row=r, column=1, sticky='ew', padx=5)
                self.preview_label = tk.Label(frame)
                self.preview_label.grid(row=r+1, column=0, columnspan=3)
                self._update_preview(var.get())

            elif ftype == "/Btn":
                var = BooleanVar(value=False)
                cb = tk.Checkbutton(frame, variable=var)
                cb.grid(row=r, column=1, sticky='w', padx=5)

            else:
                var = tk.StringVar()
                ent = tk.Entry(frame, textvariable=var)
                ent.grid(row=r, column=1, sticky='ew', padx=5)

            # expand column
            frame.grid_columnconfigure(1, weight=1)
            # store
            self.field_vars[norm] = var
            self.pdf_map[norm] = name
            # next row
            self.row[grp] += 2 if norm=='label_type' else 1

    def _recalc(self):
        try:
            q   = self.field_vars['qty'].get()
            l   = self.field_vars['lpr'].get() or 1
            ov  = self.field_vars['overage'].get()/100.0
            rolls = ceil(q/l)
            self.field_vars['rolls'].set(rolls)
            prod  = int(q + q*ov)
            self.field_vars['production_qty'].set(prod)
        except:
            pass

    def _update_preview(self, choice):
        path = LABEL_PREVIEWS.get(choice)
        if path and Path(path).exists():
            img = tk.PhotoImage(file=path)
            self.preview_photo = img
            self.preview_label.config(image=img)
        else:
            self.preview_label.config(image='')

    def save_filled(self):
        tpl = self.pdf_path.get()
        if not tpl:
            messagebox.showwarning("Missing", "Select a PDF first.")
            return
        data = {}
        for norm, var in self.field_vars.items():
            val = var.get()
            if isinstance(var, BooleanVar):
                data[self.pdf_map[norm]] = "Yes" if val else "Off"
            else:
                data[self.pdf_map[norm]] = str(val)
        out = Path(tpl).with_name(f"{Path(tpl).stem}_filled.pdf")
        try:
            self.fill_pdf(tpl, data, str(out))
            # open file
            if sys.platform.startswith('win'):
                os.startfile(str(out))
            elif sys.platform.startswith('darwin'):
                os.system(f'open "{out}"')
            else:
                os.system(f'xdg-open "{out}"')
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error", f"{type(e).__name__}: {e}")

    @staticmethod
    def fill_pdf(input_pdf, data_dict, output_pdf):
        reader = PdfReader(input_pdf)
        writer = PdfWriter()
        writer.append_pages_from_reader(reader)
        root = reader.trailer['/Root']
        if '/AcroForm' in root:
            acro = root['/AcroForm']
            writer._root_object.update({NameObject('/AcroForm'): acro})
            writer._root_object['/AcroForm'].update({NameObject('/NeedAppearances'): BooleanObject(True)})
            # bump font size
            old_da = acro.get(NameObject('/DA'), '')
            try:
                parts = old_da.split()
                font, size, *_ = parts
                new_da = f"{font} {int(size)+1} Tf {' '.join(parts[3:])}"
            except:
                new_da = '/Helv 12 Tf 0 g'
            writer._root_object['/AcroForm'].update({NameObject('/DA'): TextStringObject(new_da)})
        for page in writer.pages:
            writer.update_page_form_field_values(page, data_dict)
            if '/Annots' in page:
                for ann in page['/Annots']:
                    annot = ann.get_object()
                    if annot.get('/Subtype')=='/Widget' and annot.get('/T') in data_dict:
                        val = data_dict[annot['/T']]
                        ap  = annot.get('/AP',{}).get('/N',{})
                        if isinstance(ap, dict):
                            on = [k for k in ap.keys() if k != '/Off']
                            if on:
                                annot.update({NameObject('/AS'): NameObject(on[0] if val!='Off' else '/Off')})
        with open(output_pdf,'wb') as f:
            writer.write(f)

if __name__ == '__main__':
    DynamicPDFFormFiller().mainloop()
