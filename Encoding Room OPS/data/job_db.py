import sqlite3
import os
from util import get_current_shift_and_dbdate, JOB_DB_DIR
import glob

def get_shift_db_path():
    """Return (dbfile_path, shift_name, db_date)"""
    pattern = os.path.join(JOB_DB_DIR, "*.db")
    db_files = glob.glob(pattern)
    if not db_files:
        return None
    latest = max(db_files, key=os.path.getmtime)
    return latest

class ShiftJobDB:
    def __init__(self, dbpath):
        self.dbpath = dbpath
        os.makedirs(os.path.dirname(dbpath), exist_ok=True)
        self.conn = sqlite3.connect(self.dbpath)
        self.ensure_tables()

    def ensure_tables(self):
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT,
                job_ticket TEXT,
                customer TEXT,
                label_size TEXT,
                qty INTEGER,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                checklist_json TEXT,
                folder_path TEXT
            )
        """)
        self.conn.commit()

    def add_job(self, job):
        c = self.conn.cursor()
        import json
        c.execute(
            """INSERT INTO jobs
                (job_name, job_ticket, customer, label_size, qty, status, checklist_json, folder_path)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                job.name,
                job.code,
                job.checklist_data.get('customer', ''),
                job.checklist_data.get('label_size', ''),
                job.qty,
                getattr(job, 'status', 'Initialized'),
                json.dumps(getattr(job, 'checklist_data', {})),
                getattr(job, 'folder_path', '')
            )
        )
        self.conn.commit()
        return c.lastrowid

    def update_job(self, job, job_id):
        c = self.conn.cursor()
        import json
        c.execute(
            """UPDATE jobs SET
                status=?, checklist_json=?, folder_path=?
               WHERE id=?""",
            (
                getattr(job, 'status', 'Initialized'),
                json.dumps(getattr(job, 'checklist_data', {})),
                getattr(job, 'folder_path', ''),
                job_id
            )
        )
        self.conn.commit()

    def list_jobs(self):
        c = self.conn.cursor()
        c.execute("SELECT id, job_name, job_ticket, customer, label_size, qty, status, folder_path, checklist_json FROM jobs")
        rows = c.fetchall()
        import json
        jobs = []
        for r in rows:
            jobs.append({
                "id": r[0],
                "job_name": r[1],
                "job_ticket": r[2],
                "customer": r[3],
                "label_size": r[4],
                "qty": r[5],
                "status": r[6],
                "folder_path": r[7],
                "checklist_data": json.loads(r[8] if r[8] else '{}')
            })
        return jobs