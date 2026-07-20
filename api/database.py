import sqlite3
from datetime import datetime
import os

DB_PATH = "data/scans.db"


def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            score INTEGER NOT NULL,
            verdict TEXT NOT NULL,
            scanned_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def log_scan(url: str, score: int, verdict: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO scans (url, score, verdict, scanned_at) VALUES (?, ?, ?, ?)",
        (url, score, verdict, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_recent_scans(limit: int = 50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM scans ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_stats():
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM scans").fetchone()[0]
    flagged = conn.execute(
        "SELECT COUNT(*) FROM scans WHERE verdict = 'phishing'"
    ).fetchone()[0]
    conn.close()
    return {"total_scans": total, "flagged_count": flagged}