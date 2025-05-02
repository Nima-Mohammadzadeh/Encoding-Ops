#extract_all_code.py
import os

# Set the root directory (change this if necessary)
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

# List to store tuples of (file_path, code_text)
py_files_code = []

# Walk through the project directory tree
for foldername, subfolders, files in os.walk(ROOT_DIR):
    for filename in files:
        if filename.endswith('.py'):
            file_path = os.path.join(foldername, filename)
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin1') as f:
                    code = f.read()
            rel_path = os.path.relpath(file_path, ROOT_DIR)
            py_files_code.append((rel_path, code))

# Output to stdout (you can redirect to a file if you wish)
for rel_path, code in py_files_code:
    print('#' * 60)
    print(f'# File: {rel_path}')
    print('#' * 60)
    print(code)
    print('\n\n')