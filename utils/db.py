import sqlite3


DB_NAME = "database.db"


def init_db():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_name TEXT,
            invoice_number TEXT,
            date TEXT,
            tax TEXT,
            total TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def insert_invoice(data):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO invoices (
            vendor_name,
            invoice_number,
            date,
            tax,
            total
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            data["vendor_name"],
            data["invoice_number"],
            data["date"],
            data["tax"],
            data["total"]
        )
    )

    conn.commit()
    conn.close()


def get_all_invoices():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM invoices")

    data = cursor.fetchall()

    conn.close()

    return data