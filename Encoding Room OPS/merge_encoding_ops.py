#!/usr/bin/env python3
"""
merge_encoding_ops.py

Usage:
  python merge_encoding_ops.py

This script merges a predefined list of Python files for the Encoding Room OPS
project into a single text file, with separators indicating each file name.
"""
import os

# List of Python files to merge
FILE_PATHS = [
    r"C:\Users\Encoding 3\Desktop\Encoding Room OPS\jobs_module.py",
    r"C:\Users\Encoding 3\Desktop\Encoding Room OPS\main.py",
    r"C:\Users\Encoding 3\Desktop\Encoding Room OPS\module_selector.py",
    r"C:\Users\Encoding 3\Desktop\Encoding Room OPS\reports.py",
    r"C:\Users\Encoding 3\Desktop\Encoding Room OPS\roll_tracker.py",
    r"C:\Users\Encoding 3\Desktop\Encoding Room OPS\settings.py",
    r"C:\Users\Encoding 3\Desktop\Encoding Room OPS\test_print.py",
    r"C:\Users\Encoding 3\Desktop\Encoding Room OPS\util.py",
    r"C:\Users\Encoding 3\Desktop\Encoding Room OPS\bartender_step.py",
    r"C:\Users\Encoding 3\Desktop\Encoding Room OPS\config.py",
    r"C:\Users\Encoding 3\Desktop\Encoding Room OPS\dashboard.py",
    r"C:\Users\Encoding 3\Desktop\Encoding Room OPS\database_generator.py",
    r"C:\Users\Encoding 3\Desktop\Encoding Room OPS\docs_export.py",
    r"C:\Users\Encoding 3\Desktop\Encoding Room OPS\encoding_checklist.py",
    r"C:\Users\Encoding 3\Desktop\Encoding Room OPS\jobdata.py"
]

# Output file name
OUTPUT_PATH = "merged_encoding_ops.txt"

def merge_files(paths, output):
    with open(output, 'w', encoding='utf-8') as out_file:
        for path in paths:
            filename = os.path.basename(path)
            out_file.write(f"# === File: {filename} ===\n")
            try:
                with open(path, 'r', encoding='utf-8') as in_file:
                    out_file.write(in_file.read())
            except Exception as e:
                out_file.write(f"# Error reading {filename}: {e}\n")
            out_file.write("\n\n")

def main():
    merge_files(FILE_PATHS, OUTPUT_PATH)
    print(f"Merged {len(FILE_PATHS)} files into {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
