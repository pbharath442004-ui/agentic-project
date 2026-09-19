"""Deterministic seed data for the business database.

Produces a realistic 12-month window of fintech activity anchored to "now"
so period-relative questions ("last month", "this quarter") always have data.
Uses a fixed RNG seed so the dataset is reproducible.

Guarantees relevant to the task brief:
* `user_123` exists and has at least one OPEN dispute.
* `john@example.com` exists as an invoice customer.
* Sizable sales volume in the current + previous calendar month.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import List

FIRST = ["Aarav", "Emma", "Liam", "Priya", "Noah", "Sofia", "Arjun", "Mia", "Ethan", "Zara",
         "Lucas", "Ivy", "Omar", "Nina", "Kai", "Lena", "Ravi", "Clara", "Diego", "Hana",
         "Felix", "Aisha", "Marco", "Yuki", "Tom", "Ines", "Vikram", "Elsa", "Rohan", "Grace"]
LAST = ["Sharma", "Miller", "Patel", "Kim", "Garcia", "Chen", "Kumar", "Brown", "Singh", "Lee",
        "Silva", "Novak", "Haddad", "Costa", "Tanaka", "Weber", "Iyer", "Morales", "Khan", "Olsen"]
COUNTRIES = ["US", "IN", "GB", "DE", "SG", "AU", "CA", "AE", "MX", "FR"]
COUNTRY_W = [30, 22, 10, 8, 7, 6, 5, 4, 4, 4]
CURRENCIES = ["USD", "EUR", "GBP", "INR", "SGD"]
INVOICE_DESC = [
    "Consulting services — Q{s}", "SaaS subscription (annual)", "Product license — tier {t}",
    "Integration support retainer", "Onboarding professional services", "API usage overage",
    "Enterprise support plan", "Custom development sprint {s}", "Training & certification",
    "Marketplace services fee", "Data processing fees", "White-glove migration",
]
PAY_METHODS = ["card", "bank_transfer", "balance", "wallet"]
DISPUTE_REASONS = ["unauthorized_transaction", "item_not_received", "duplicate_charge",
                   "defective_product", "not_as_described", "other"]
TICKET_SUBJECTS = [
    "Payment failed but amount deducted", "Invoice PDF missing logo", "Webhook not firing",
    "Dispute evidence upload issue", "FX rate discrepancy", "Refund timeline question",
    "API rate limit errors", "Duplicate customer record", "Report export timeout",
    "Subscription proration question",
]


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def seed(db, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    rng = random.Random(42)
    t0 = now - timedelta(days=365)

    # --- users -------------------------------------------------------------
    users: List[dict] = []
    for i in range(100, 350):  # user_100 .. user_349  (includes user_123)
        first, last = rng.choice(FIRST), rng.choice(LAST)
        users.append({
            "id": f"user_{i}",
            "name": f"{first} {last}",
            "email": f"{first.lower()}.{last.lower()}{i}@example.com",
            "country": rng.choices(COUNTRIES, COUNTRY_W, k=1)[0],
            "created_at": _iso(t0 + timedelta(days=rng.randint(0, 365))),
        })
    db.execute("DELETE FROM users")
    db.conn.executemany(
        "INSERT INTO users (id, name, email, country, created_at) VALUES (?,?,?,?,?)",
        [(u["id"], u["name"], u["email"], u["country"], u["created_at"]) for u in users],
    )
    user_ids = [u["id"] for u in users]

    # --- invoices ----------------------------------------------------------
    inv_status = ["paid", "paid", "paid", "paid", "sent", "sent", "overdue", "draft", "cancelled"]
    invoices = []
    for i in range(1, 421):
        user_id = rng.choice(user_ids)
        amount = round(rng.uniform(10, 2500), 2)
        currency = rng.choices(CURRENCIES, [70, 10, 6, 9, 5], k=1)[0]
        status = rng.choice(inv_status)
        issued = t0 + timedelta(days=rng.randint(0, 364), hours=rng.randint(0, 23))
        due = issued + timedelta(days=rng.randint(14, 45))
        desc = rng.choice(INVOICE_DESC).format(s=rng.randint(1, 4), t=rng.choice(["Pro", "Enterprise", "Basic"]))
        items = [
            {"name": "Service fee", "qty": 1, "price": round(amount * 0.8, 2)},
            {"name": "Taxes & charges", "qty": 1, "price": round(amount * 0.2, 2)},
        ]
        invoices.append((
            f"INV-{i:04d}", user_id, f"customer{1000 + i}@example.com", amount, currency, status,
            desc, str(items), _iso(issued), _iso(due),
            _iso(issued + timedelta(days=1)) if status in ("paid", "sent", "overdue") else None,
            _iso(issued + timedelta(days=rng.randint(1, 10))) if status == "paid" else None,
        ))
    # The task's example customer
    invoices[-1] = (
        "INV-0420", "user_123", "john@example.com", 50.0, "USD", "sent",
        "Consulting services — Q3", str([{"name": "Consulting", "qty": 1, "price": 50.0}]),
        _iso(now - timedelta(days=20)), _iso(now + timedelta(days=20)), _iso(now - timedelta(days=19)), None,
    )
    db.execute("DELETE FROM invoices")
    db.conn.executemany(
        "INSERT INTO invoices (id, user_id, customer_email, amount, currency, status, description,"
        " items, issued_at, due_at, sent_at, paid_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        invoices,
    )

    # --- payments ------------------------------------------------------------
    pay_status = ["succeeded", "succeeded", "succeeded", "succeeded", "succeeded",
                  "pending", "failed", "refunded"]
    payments = []
    paid_invoices = [inv for inv in invoices if inv[5] == "paid"]
    for i in range(1, 521):
        user_id = rng.choice(user_ids)
        invoice = rng.choice(paid_invoices) if (paid_invoices and rng.random() < 0.4) else None
        amount = round(rng.uniform(5, 3000), 2)
        created = t0 + timedelta(days=rng.randint(0, 364), hours=rng.randint(0, 23))
        payments.append((
            f"PAY-{i:04d}", user_id, invoice[0] if invoice else None, amount, invoice[4] if invoice else "USD",
            rng.choice(PAY_METHODS), rng.choice(pay_status), _iso(created),
        ))
    db.execute("DELETE FROM payments")
    db.conn.executemany(
        "INSERT INTO payments (id, user_id, invoice_id, amount, currency, method, status, created_at)"
        " VALUES (?,?,?,?,?,?,?,?)",
        payments,
    )

    # --- disputes -------------------------------------------------------------
    dsp_status = ["open", "open", "under_review", "under_review", "won", "lost", "closed"]
    disputes = []
    for i in range(1, 81):
        user_id = rng.choice(user_ids)
        pay = rng.choice(payments)
        opened = t0 + timedelta(days=rng.randint(30, 364))
        disputes.append((
            f"DSP-{i:04d}", user_id, pay[0], rng.choice(DISPUTE_REASONS), rng.choice(dsp_status),
            _iso(opened), _iso(opened + timedelta(days=rng.randint(0, 20))),
        ))
    # Guaranteed: user_123 has an open dispute + one under review (task example)
    disputes.append(("DSP-0081", "user_123", payments[5][0], "duplicate_charge", "open",
                     _iso(now - timedelta(days=40)), _iso(now - timedelta(days=38))))
    disputes.append(("DSP-0082", "user_123", payments[6][0], "item_not_received", "under_review",
                     _iso(now - timedelta(days=12)), _iso(now - timedelta(days=2))))
    db.execute("DELETE FROM disputes")
    db.conn.executemany(
        "INSERT INTO disputes (id, user_id, payment_id, reason, status, opened_at, last_update_at)"
        " VALUES (?,?,?,?,?,?,?)",
        disputes,
    )

    # --- transactions (GMV source of truth) ------------------------------------
    tx_types = ["sale"] * 7 + ["refund", "fee", "payout"]
    txns = []
    for i in range(1, 901):
        user_id = rng.choice(user_ids)
        ttype = rng.choice(tx_types)
        amount = round(rng.uniform(5, 4000), 2) if ttype == "sale" else round(rng.uniform(2, 900), 2)
        created = t0 + timedelta(days=rng.randint(0, 364), hours=rng.randint(0, 23))
        txns.append((f"TXN-{i:05d}", user_id, ttype, amount, "USD", _iso(created)))
    db.execute("DELETE FROM transactions")
    db.conn.executemany(
        "INSERT INTO transactions (id, user_id, type, amount, currency, created_at) VALUES (?,?,?,?,?,?)",
        txns,
    )

    # --- webhooks / tickets / FX ------------------------------------------------
    wh_events = [["invoice.paid"], ["payment.captured"], ["dispute.opened"],
                 ["payment.refunded"], ["invoice.paid", "payment.captured"]]
    webhooks = [
        (f"WHK-{i:03d}", f"https://hooks.example.com/datazoic/{i}",
         str(rng.choice(wh_events)), rng.random() < 0.85)
        for i in range(1, 25)
    ]
    db.execute("DELETE FROM webhooks")
    db.conn.executemany(
        "INSERT INTO webhooks (id, url, events, active) VALUES (?,?,?,?)", webhooks
    )

    tickets = []
    for i in range(1, 61):
        user_id = rng.choice(user_ids)
        created = t0 + timedelta(days=rng.randint(0, 364))
        tickets.append((
            f"TKT-{i:04d}", user_id, rng.choice(TICKET_SUBJECTS),
            rng.choice(["open", "in_progress", "closed", "closed"]),
            rng.choice(["low", "medium", "high", "urgent"]), _iso(created),
        ))
    db.execute("DELETE FROM tickets")
    db.conn.executemany(
        "INSERT INTO tickets (id, user_id, subject, status, priority, created_at) VALUES (?,?,?,?,?,?)",
        tickets,
    )

    rates = {"EUR": 0.92, "GBP": 0.79, "INR": 83.4, "SGD": 1.34, "AUD": 1.52, "CAD": 1.37,
             "JPY": 149.2, "AED": 3.67, "MXN": 18.1, "CHF": 0.88, "SEK": 10.4, "NZD": 1.66,
             "ZAR": 18.9, "CNY": 7.25, "KRW": 1385.0}
    db.execute("DELETE FROM exchange_rates")
    db.conn.executemany(
        "INSERT INTO exchange_rates (base, quote, rate, updated_at) VALUES (?,?,?,?)",
        [("USD", q, r, _iso(now)) for q, r in rates.items()],
    )

    db.conn.commit()
    return {t: db.count(t) for t in ("users", "invoices", "payments", "disputes",
                                     "transactions", "webhooks", "tickets", "exchange_rates")}
