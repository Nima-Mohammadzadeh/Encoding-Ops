#!/usr/bin/env python3
"""
extract_label_sizes.py

Usage:
  python extract_label_sizes.py root_directory -o output.txt

This script traverses each customer folder under the given root directory,
collects subfolder names that represent label sizes (e.g., '1.85 x .91'),
rounds dimensions to two decimal places, removes duplicates, and writes
the sorted list to the output text file.
"""

import os
import re
import argparse

def extract_sizes(root_dir):
    sizes = set()
    # Loop over each customer directory
    for customer in os.listdir(root_dir):
        cust_path = os.path.join(root_dir, customer)
        if not os.path.isdir(cust_path):
            continue
        # Loop over subdirectories inside each customer folder
        for item in os.listdir(cust_path):
            size_path = os.path.join(cust_path, item)
            if os.path.isdir(size_path):
                # Extract numeric parts from the folder name
                parts = re.findall(r"[0-9]*\.?[0-9]+", item)
                if len(parts) >= 2:
                    try:
                        w = round(float(parts[0]), 2)
                        h = round(float(parts[1]), 2)
                        sizes.add(f"{w:.2f} x {h:.2f}")
                    except ValueError:
                        continue
    return sizes

def main():
    parser = argparse.ArgumentParser(description="Extract unique label sizes from directory structure.")
    parser.add_argument('root', help="Root directory containing customer folders.")
    parser.add_argument('-o', '--output', default='label_sizes.txt', help="Output text file path.")
    args = parser.parse_args()

    sizes = extract_sizes(args.root)
    # Sort by numeric width then height
    sorted_sizes = sorted(
        sizes,
        key=lambda s: tuple(map(float, re.findall(r"[0-9]*\.?[0-9]+", s)))
    )

    with open(args.output, 'w', encoding='utf-8') as f:
        for size in sorted_sizes:
            f.write(size + '\n')

    print(f"Extracted {len(sorted_sizes)} unique sizes to {args.output}")

if __name__ == '__main__':
    main()
