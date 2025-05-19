import tkinter as tk
from tkinter import filedialog, messagebox
import os

class CodeCombinerApp:
    def __init__(self, master):
        self.master = master
        master.title("Python File Combiner")
        master.geometry("450x170")
        
        self.files = []
        
        # Button to select files
        self.select_btn = tk.Button(master, text="Add Python Files", command=self.select_files)
        self.select_btn.pack(pady=(15, 5))
        
        # Button to clear selection
        self.clear_btn = tk.Button(master, text="Clear Selection", command=self.clear_selection, state=tk.DISABLED)
        self.clear_btn.pack(pady=5)
        
        # Label to show count
        self.count_label = tk.Label(master, text="No files selected")
        self.count_label.pack(pady=5)
        
        # Button to combine into text
        self.combine_btn = tk.Button(master, text="Combine into TXT", command=self.combine_files, state=tk.DISABLED)
        self.combine_btn.pack(pady=5)

    def select_files(self):
        new_files = filedialog.askopenfilenames(
            title="Choose Python files",
            filetypes=[("Python Files", "*.py")],
        )
        # Add only unique paths
        added = 0
        for f in new_files:
            if f not in self.files:
                self.files.append(f)
                added += 1
        
        if added:
            self.count_label.config(text=f"{len(self.files)} file(s) selected")
            self.combine_btn.config(state=tk.NORMAL)
            self.clear_btn.config(state=tk.NORMAL)
        # if no new files, do nothing

    def clear_selection(self):
        self.files.clear()
        self.count_label.config(text="No files selected")
        self.combine_btn.config(state=tk.DISABLED)
        self.clear_btn.config(state=tk.DISABLED)

    def combine_files(self):
        if not self.files:
            return

        # Use directory of first selected file for output
        out_dir = os.path.dirname(self.files[0])
        out_path = os.path.join(out_dir, "combined_code.txt")

        try:
            with open(out_path, "w", encoding="utf-8") as out_file:
                for filepath in self.files:
                    filename = os.path.basename(filepath)
                    out_file.write(f"# ===== {filename} =====\n\n")
                    with open(filepath, "r", encoding="utf-8") as f:
                        out_file.write(f.read())
                    out_file.write("\n\n")  # spacer between files

            messagebox.showinfo("Success", f"Combined code saved to:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write file:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CodeCombinerApp(root)
    root.mainloop()
