import os
import tkinter as tk
from tkinter import filedialog, messagebox

def write_directory_tree(root_dir, out_path):
    with open(out_path, 'w', encoding='utf-8') as f:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Indent based on depth
            depth = dirpath[len(root_dir):].count(os.sep)
            indent = '    ' * depth
            f.write(f"{indent}{os.path.basename(dirpath)}/\n")
            for filename in filenames:
                f.write(f"{indent}    {filename}\n")

def select_and_write_tree():
    folder = filedialog.askdirectory(title="Select a folder to scan")
    if not folder:
        return
    out_path = os.path.join(folder, "directory_tree.txt")
    write_directory_tree(folder, out_path)
    messagebox.showinfo("Done", f"Directory tree saved to:\n{out_path}")

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide main window, show only file dialog
    select_and_write_tree()
