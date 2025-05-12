import os

# Set root directory to current script location
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
OUTPUT_FILE = os.path.join(ROOT_DIR, 'all_python_code_dump.txt')

# Storage
py_files_code = []
expected_py_files = []
skipped_files = {}

# Walk through the full directory tree
for foldername, subfolders, files in os.walk(ROOT_DIR):
    for filename in files:
        if filename.lower().strip().endswith('.py'):
            file_path = os.path.join(foldername, filename)
            rel_path = os.path.relpath(file_path, ROOT_DIR)
            expected_py_files.append(rel_path)
            print(f"[+] Found: {rel_path}")
            try:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='latin1') as f:
                        code = f.read()
                py_files_code.append((rel_path, code))
            except Exception as e:
                skipped_files[rel_path] = str(e)

# Write all output to a .txt file
with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
    for rel_path, code in py_files_code:
        out.write('#' * 60 + '\n')
        out.write(f'# File: {rel_path}\n')
        out.write('#' * 60 + '\n')
        out.write(code if code.strip() else '[Empty file]')
        out.write('\n\n\n')

    if skipped_files:
        out.write('\n' + '=' * 60 + '\n')
        out.write('⚠️ Skipped Files Due to Errors:\n')
        out.write('=' * 60 + '\n')
        for path, reason in skipped_files.items():
            out.write(f'{path} --> {reason}\n')

print(f"\n✅ Extraction complete. Output saved to: {OUTPUT_FILE}")
