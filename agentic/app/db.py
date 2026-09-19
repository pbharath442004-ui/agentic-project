import sqlite3
from pathlib import Path
from .config import DATABASE_PATH

def connect():
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DATABASE_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id TEXT PRIMARY KEY,
            customer TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            cancelled_at TEXT
        );
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            invoice_id TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS disputes (
            dispute_id TEXT PRIMARY KEY,
            invoice_id TEXT NOT NULL,
            status TEXT NOT NULL,
            reason TEXT,
            created_at TEXT NOT NULL
        );
        """)
