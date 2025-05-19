# data/job_db.py

import sqlite3
import os
import json

JOBS_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "jobs_db", "jobs.db")
)
os.makedirs(os.path.dirname(JOBS_DB_PATH), exist_ok=True)

def get_db_path():
    return JOBS_DB_PATH

class JobDB:
    def __init__(self, db_path=None):
        self.db_path = db_path or get_db_path()
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
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
            )""")
        self.conn.commit()

    def add_job(self, job):
        c = self.conn.cursor()
        c.execute("""INSERT INTO jobs
                        (job_name, job_ticket, customer, label_size, qty, status, checklist_json, folder_path)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                  (job.name, job.code, job.checklist_data.get('customer', ''),
                   job.checklist_data.get('label_size', ''), job.qty,
                   getattr(job, 'status', 'active'),  # Default: active
                   json.dumps(getattr(job, 'checklist_data', {})),
                   getattr(job, 'folder_path', '')))
        self.conn.commit()
        return c.lastrowid

    def update_job(self, job, job_id):
        c = self.conn.cursor()
        c.execute("""UPDATE jobs SET
                            status=?, checklist_json=?, folder_path=?
                     WHERE id=?""",
                  (getattr(job, 'status', 'active'),
                   json.dumps(getattr(job, 'checklist_data', {})),
                   getattr(job, 'folder_path', ''),
                   job_id
                  ))
        self.conn.commit()

    def delete_job(self, job_id):
        c = self.conn.cursor()
        c.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        self.conn.commit()
        
    def mark_job_completed(self, job_id):
        c = self.conn.cursor()
        c.execute("UPDATE jobs SET status = 'completed' WHERE id = ?", (job_id,))
        self.conn.commit()

    def list_active_jobs(self):
        c = self.conn.cursor()
        c.execute("SELECT id, job_name, job_ticket, customer, label_size, qty, status, folder_path, checklist_json FROM jobs WHERE status <> 'completed'")
        return self._convert_rows(c.fetchall())

    def list_completed_jobs(self):
        c = self.conn.cursor()
        c.execute("SELECT id, job_name, job_ticket, customer, label_size, qty, status, folder_path, checklist_json FROM jobs WHERE status = 'completed'")
        return self._convert_rows(c.fetchall())


    def list_jobs(self):
        c = self.conn.cursor()
        c.execute("SELECT id, job_name, job_ticket, customer, label_size, qty, status, folder_path, checklist_json FROM jobs")
        rows = c.fetchall()
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
    
    def list_completed_jobs(self):
        c = self.conn.cursor()
        c.execute("SELECT id, job_name, job_ticket, customer, label_size, qty, status, folder_path, checklist_json FROM jobs WHERE status = 'completed'")
        return self._convert_rows(c.fetchall())
    
    def _convert_rows(self, rows):  # Helper for both list_active and list_completed
        import json
        jobs = []
        for r in rows:
            jobs.append({
                "id": r[0], "job_name": r[1], "job_ticket": r[2],
                "customer": r[3], "label_size": r[4], "qty": r[5],
                "status": r[6], "folder_path": r[7],
                "checklist_data": json.loads(r[8] if r[8] else '{}')
            })
        return jobs