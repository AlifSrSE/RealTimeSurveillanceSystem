# db.py
import os
import sqlite3

def init_db(db_path="logs/analytics.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS traffic_logs (
            time TEXT,
            camera_id TEXT,
            in_count INTEGER,
            out_count INTEGER,
            posture TEXT,
            alert TEXT
        )
    ''')
    conn.commit()
    return conn

def insert_log(conn, log_entry):
    c = conn.cursor()
    c.execute('''
        INSERT INTO traffic_logs (time, camera_id, in_count, out_count, posture, alert)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        log_entry["time"],
        log_entry["camera_id"],
        log_entry["in"],
        log_entry["out"],
        log_entry["posture"],
        log_entry["alert"]
    ))
    conn.commit()
