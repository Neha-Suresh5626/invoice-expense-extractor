"""
utils/db.py — SQLite operations
Tables: users, invoices
"""
import sqlite3
from datetime import datetime

DB_NAME = "database.db"


def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT    UNIQUE NOT NULL,
            password  TEXT    NOT NULL,
            created_at TEXT
        )
    """)

    # Invoices table
    c.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER,
            vendor_name     TEXT    DEFAULT 'Not Available',
            invoice_number  TEXT    DEFAULT 'Not Available',
            date            TEXT    DEFAULT 'Not Available',
            due_date        TEXT    DEFAULT 'Not Available',
            tax             TEXT    DEFAULT '0',
            gst             TEXT    DEFAULT '0',
            total           TEXT    DEFAULT '0',
            subtotal        TEXT    DEFAULT '0',
            currency        TEXT    DEFAULT 'INR',
            category        TEXT    DEFAULT 'General',
            invoice_type    TEXT    DEFAULT 'typed',
            filename        TEXT,
            raw_text        TEXT,
            created_at      TEXT
        )
    """)
    conn.commit()
    conn.close()


# ── User ops ─────────────────────────────────────────────────────────

def create_user(username, password_hash):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (username, password, created_at) VALUES (?,?,?)",
            (username, password_hash, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False   # username taken
    finally:
        conn.close()


def get_user(username):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Invoice ops ───────────────────────────────────────────────────────

def insert_invoice(data, user_id):
    conn = get_conn()
    conn.execute("""
        INSERT INTO invoices
            (user_id, vendor_name, invoice_number, date, due_date,
             tax, gst, total, subtotal, currency, category,
             invoice_type, filename, raw_text, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        user_id,
        data.get("vendor_name", "Not Available"),
        data.get("invoice_number", "Not Available"),
        data.get("date", "Not Available"),
        data.get("due_date", "Not Available"),
        str(data.get("tax", "0")),
        str(data.get("gst", "0")),
        str(data.get("total", "0")),
        str(data.get("subtotal", "0")),
        data.get("currency", "INR"),
        data.get("category", "General"),
        data.get("invoice_type", "typed"),
        data.get("filename", ""),
        data.get("raw_text", ""),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ))
    conn.commit()
    conn.close()


def get_all_invoices(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM invoices WHERE user_id=? ORDER BY id DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_invoice(inv_id, user_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM invoices WHERE id=? AND user_id=?", (inv_id, user_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Analytics queries ─────────────────────────────────────────────────

def get_summary(user_id):
    conn = get_conn()
    row = conn.execute("""
        SELECT
            COUNT(*)                              AS total_invoices,
            COALESCE(SUM(CAST(total AS REAL)), 0) AS total_spend,
            COALESCE(SUM(CAST(gst AS REAL)),   0) AS total_gst,
            COALESCE(AVG(CAST(total AS REAL)),  0) AS avg_invoice
        FROM invoices WHERE user_id=?
    """, (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


def get_by_category(user_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT category,
               COUNT(*) AS cnt,
               COALESCE(SUM(CAST(total AS REAL)),0) AS total
        FROM invoices WHERE user_id=?
        GROUP BY category ORDER BY total DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_by_vendor(user_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT vendor_name,
               COUNT(*) AS cnt,
               COALESCE(SUM(CAST(total AS REAL)),0) AS total
        FROM invoices WHERE user_id=?
        GROUP BY vendor_name ORDER BY total DESC LIMIT 10
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_by_month(user_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT SUBSTR(created_at,1,7) AS month,
               COUNT(*) AS cnt,
               COALESCE(SUM(CAST(total AS REAL)),0) AS total
        FROM invoices WHERE user_id=?
        GROUP BY month ORDER BY month
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_gst_summary(user_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT vendor_name,
               COALESCE(SUM(CAST(gst AS REAL)),0) AS total_gst,
               COALESCE(SUM(CAST(total AS REAL)),0) AS total_amount
        FROM invoices WHERE user_id=?
        GROUP BY vendor_name ORDER BY total_gst DESC LIMIT 10
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]