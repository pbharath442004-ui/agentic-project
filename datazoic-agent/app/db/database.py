"""Business database access layer (SQLite).

Holds the *operational* data the agent's tools query — invoices, payments,
disputes, transactions, customers, tickets, webhooks, FX rates. This is
separate from the RAG vector store: tools act on business state, the RAG
tool answers knowledge questions.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    country TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS invoices (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL,
    description TEXT,
    items TEXT,
    issued_at TEXT NOT NULL,
    due_at TEXT,
    sent_at TEXT,
    paid_at TEXT
);
CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    invoice_id TEXT,
    amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    method TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS disputes (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    payment_id TEXT,
    reason TEXT NOT NULL,
    status TEXT NOT NULL,
    opened_at TEXT NOT NULL,
    last_update_at TEXT
);
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,           -- sale | refund | fee | payout
    amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS webhooks (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    events TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    subject TEXT NOT NULL,
    status TEXT NOT NULL,
    priority TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS exchange_rates (
    base TEXT NOT NULL,
    quote TEXT NOT NULL,
    rate REAL NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (base, quote)
);
"""


class BusinessDB:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # -- generic helpers -----------------------------------------------------
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        cur = self.conn.execute(query, params)
        self.conn.commit()
        return cur

    def query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        rows = self.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def query_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(query, params).fetchone()
        return dict(row) if row else None

    def count(self, table: str) -> int:
        return int(self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

    def is_empty(self) -> bool:
        return self.count("users") == 0

    def stats(self) -> Dict[str, int]:
        tables = [
            "users", "invoices", "payments", "disputes", "transactions",
            "webhooks", "tickets", "exchange_rates",
        ]
        return {t: self.count(t) for t in tables}

    @staticmethod
    def parse_json(value, default):
        if value is None:
            return default
        try:
            return json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return default
