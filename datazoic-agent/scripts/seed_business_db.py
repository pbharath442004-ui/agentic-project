"""Seed the business SQLite database with 12 months of deterministic data.

Usage:
    python scripts/seed_business_db.py

Output: data/business.db
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import BUSINESS_DB_PATH  # noqa: E402
from app.db.database import BusinessDB  # noqa: E402
from app.db.seed import seed  # noqa: E402


def main() -> int:
    db = BusinessDB(BUSINESS_DB_PATH)
    stats = seed(db)
    print("Business database seeded at", BUSINESS_DB_PATH)
    for table, n in stats.items():
        print(f"  {table:<15} {n:5d} rows")
    # smoke checks from the task brief
    u = db.query_one("SELECT id, name, email FROM users WHERE id = 'user_123'")
    d = db.query_one("SELECT id, status, reason FROM disputes WHERE user_id='user_123' AND status='open'")
    j = db.query_one("SELECT id, customer_email, amount, status FROM invoices WHERE customer_email='john@example.com'")
    print("\nSmoke checks:")
    print("  user_123 exists:       ", bool(u), u and f"({u['name']}, {u['email']})")
    print("  user_123 open dispute: ", bool(d), d and f"({d['id']}, {d['reason']})")
    print("  john@example.com inv:  ", bool(j), j and f"({j['id']}, {j['amount']} {j['status']})")
    assert u and d and j, "seed guarantees violated"
    return 0


if __name__ == "__main__":
    sys.exit(main())
