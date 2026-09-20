import sqlite3
from datetime import datetime


DATABASE_NAME = "veridian.db"


def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT,
            issue TEXT NOT NULL,
            category TEXT,
            priority TEXT,
            status TEXT,
            resolution TEXT,
            source TEXT,
            created_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT,
            action TEXT,
            details TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def create_ticket(
    employee_name,
    issue,
    category,
    priority,
    status,
    resolution,
    source
):
    conn = get_connection()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor = conn.execute("""
        INSERT INTO tickets
        (employee_name, issue, category, priority, status,
         resolution, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        employee_name,
        issue,
        category,
        priority,
        status,
        resolution,
        source,
        created_at
    ))

    ticket_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return ticket_id


def add_audit_log(employee_name, action, details):
    conn = get_connection()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn.execute("""
        INSERT INTO audit_log
        (employee_name, action, details, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        employee_name,
        action,
        details,
        created_at
    ))

    conn.commit()
    conn.close()


def get_all_tickets():
    conn = get_connection()

    tickets = conn.execute("""
        SELECT * FROM tickets
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return tickets


def get_audit_logs():
    conn = get_connection()

    logs = conn.execute("""
        SELECT * FROM audit_log
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return logs