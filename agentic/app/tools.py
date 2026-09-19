from datetime import datetime, timezone
from uuid import uuid4
from .db import connect

def now():
    return datetime.now(timezone.utc).isoformat()

def create_invoice(customer, amount, currency="INR"):
    if amount <= 0:
        return {"success": False, "error": "Amount must be greater than zero."}
    invoice_id = "INV-" + uuid4().hex[:8].upper()
    with connect() as con:
        con.execute(
            "INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?)",
            (invoice_id, customer, amount, currency.upper(), "OPEN", now(), None)
        )
    return {"success": True, "invoice_id": invoice_id, "customer": customer,
            "amount": amount, "currency": currency.upper(), "status": "OPEN"}

def invoice_status(invoice_id):
    with connect() as con:
        row = con.execute("SELECT * FROM invoices WHERE invoice_id=?", (invoice_id,)).fetchone()
    if not row:
        return {"success": False, "error": f"Invoice {invoice_id} was not found."}
    return {"success": True, "invoice": dict(row)}

def send_payment(invoice_id, amount=None):
    with connect() as con:
        row = con.execute("SELECT * FROM invoices WHERE invoice_id=?", (invoice_id,)).fetchone()
        if not row:
            return {"success": False, "error": f"Invoice {invoice_id} was not found."}
        if row["status"] == "CANCELLED":
            return {"success": False, "error": "Cannot pay a cancelled invoice."}
        pay_amount = row["amount"] if amount is None else amount
        if pay_amount <= 0 or pay_amount > row["amount"]:
            return {"success": False, "error": "Payment amount must be positive and not exceed the invoice amount."}
        payment_id = "PAY-" + uuid4().hex[:8].upper()
        con.execute("INSERT INTO payments VALUES (?, ?, ?, ?, ?)",
                    (payment_id, invoice_id, pay_amount, "COMPLETED", now()))
        status = "PAID" if pay_amount == row["amount"] else "PARTIALLY_PAID"
        con.execute("UPDATE invoices SET status=? WHERE invoice_id=?", (status, invoice_id))
    return {"success": True, "payment_id": payment_id, "invoice_id": invoice_id,
            "amount": pay_amount, "status": "COMPLETED"}

def cancel_invoice(invoice_id):
    with connect() as con:
        row = con.execute("SELECT * FROM invoices WHERE invoice_id=?", (invoice_id,)).fetchone()
        if not row:
            return {"success": False, "error": f"Invoice {invoice_id} was not found."}
        if row["status"] == "PAID":
            return {"success": False, "error": "A paid invoice cannot be cancelled."}
        con.execute("UPDATE invoices SET status='CANCELLED', cancelled_at=? WHERE invoice_id=?",
                    (now(), invoice_id))
    return {"success": True, "invoice_id": invoice_id, "status": "CANCELLED"}

def dispute_status(invoice_id):
    with connect() as con:
        row = con.execute(
            "SELECT * FROM disputes WHERE invoice_id=? ORDER BY created_at DESC LIMIT 1",
            (invoice_id,)
        ).fetchone()
    if not row:
        return {"success": True, "invoice_id": invoice_id, "status": "NO_DISPUTE"}
    return {"success": True, "dispute": dict(row)}

def sales_report():
    with connect() as con:
        row = con.execute("""
            SELECT COUNT(*) AS invoice_count,
                   COALESCE(SUM(amount),0) AS invoiced_amount,
                   COALESCE(SUM(CASE WHEN status='PAID' THEN amount ELSE 0 END),0) AS paid_amount,
                   COALESCE(SUM(CASE WHEN status='CANCELLED' THEN amount ELSE 0 END),0) AS cancelled_amount
            FROM invoices
        """).fetchone()
    return {"success": True, "report": dict(row)}
