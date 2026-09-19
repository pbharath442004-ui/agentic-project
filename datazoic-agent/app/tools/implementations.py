"""Real implementations for the core tools (handler key "db:<name>").

Each handler takes (args: dict, ctx: dict) and returns a JSON-serializable
dict, or raises `ToolError`. `ctx` provides:
    db    -> BusinessDB
    now   -> datetime (UTC)
    registry_search(query, k) -> list of {name, domain, description}
    last_request() -> dict | None
    rag_search(query, k) -> list of {id, section, title, snippet, score}
"""
from __future__ import annotations

import csv
import hashlib
import io
import re
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

MONEY_KEYS = re.compile(r"(amount|total|sales|revenue|gmv|fee|price|balance|volume|net|cost)", re.I)


class ToolError(Exception):
    def __init__(self, message: str, missing: Optional[List[str]] = None, code: str = "error"):
        super().__init__(message)
        self.message = message
        self.missing = missing
        self.code = code


def _require(args: Dict[str, Any], *keys) -> List[str]:
    missing = [k for k in keys if args.get(k) in (None, "")]
    if missing:
        raise ToolError(f"Missing required parameter(s): {', '.join(missing)}.",
                        missing=missing, code="missing_required_parameter")
    return missing


def _num(args, key, default=None):
    v = args.get(key, default)
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        raise ToolError(f"Parameter '{key}' must be a number, got {v!r}.", code="invalid_parameter")


def _month_shift(d, delta):
    m = d.month - 1 + delta
    y = d.year + m // 12
    m = m % 12 + 1
    return d.replace(year=y, month=m, day=1)


def _resolve_period(period: Optional[str], now: datetime):
    p = (period or "last_month").lower()
    today = now.date()
    if p == "last_month":
        start = _month_shift(today, -1)
        end = today.replace(day=1)
    elif p == "this_month":
        start = today.replace(day=1)
        end = today + timedelta(days=1)
    elif p in ("last_7_days", "last_7d"):
        start = today - timedelta(days=7)
        end = today + timedelta(days=1)
    elif p == "last_30_days":
        start = today - timedelta(days=30)
        end = today + timedelta(days=1)
    elif p == "last_90_days":
        start = today - timedelta(days=90)
        end = today + timedelta(days=1)
    elif p == "ytd":
        start = today.replace(month=1, day=1)
        end = today + timedelta(days=1)
    elif p == "all_time":
        start = today.replace(year=2000, month=1, day=1)
        end = today + timedelta(days=1)
    else:
        raise ToolError(f"Unknown period '{period}'. Use one of: last_month, this_month, last_7_days, last_30_days, last_90_days, ytd, all_time.",
                        code="invalid_parameter")
    label = {
        "last_month": f"{start.strftime('%B %Y')}",
        "this_month": f"{start.strftime('%B %Y')}",
        "last_7_days": "the last 7 days",
        "last_30_days": "the last 30 days",
        "last_90_days": "the last 90 days",
        "ytd": f"year to date ({today.year})",
        "all_time": "all time",
    }[p]
    return start, end, label


def _range_where(start, end, column="created_at"):
    return (f"{column} >= ? AND {column} < ?",
            (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")))


def _uid(args: Dict, default: str = "user_123") -> str:
    v = args.get("user_id") or default
    v = str(v).strip()
    m = re.search(r"user[_-]?(\d+)", v, re.I)
    return f"user_{m.group(1)}" if m else v


# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------

def create_invoice(args, ctx):
    _require(args, "customer_email", "amount")
    db = ctx["db"]
    amount = _num(args, "amount")
    if amount is None or amount <= 0:
        raise ToolError("amount must be a positive number.", code="invalid_parameter")
    user_id = _uid(args)
    seq = db.query_one("SELECT COALESCE(MAX(CAST(substr(id, 5) AS INTEGER)), 0) + 1 AS n FROM invoices")["n"]
    inv_id = f"INV-{seq:04d}"
    now = ctx["now"]
    db.execute(
        "INSERT INTO invoices (id, user_id, customer_email, amount, currency, status, description, items, issued_at, due_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?)",
        (inv_id, user_id, str(args["customer_email"]), round(amount, 2),
         args.get("currency") or "USD", "draft", args.get("description") or "",
         f'[{{"name": "{args.get("description") or "Service fee"}", "qty": 1, "price": {round(amount, 2)}}}]',
         now.strftime("%Y-%m-%dT%H:%M:%SZ"), (now + timedelta(days=30)).strftime("%Y-%m-%d")),
    )
    return get_invoice({"invoice_id": inv_id}, ctx) | {"message": f"Invoice {inv_id} created for {args['customer_email']}."}


def list_invoices(args, ctx):
    db = ctx["db"]
    where, params = [], []
    if args.get("user_id"):
        where.append("user_id = ?"); params.append(_uid(args))
    if args.get("status"):
        where.append("status = ?"); params.append(args["status"])
    limit = min(int(args.get("limit") or 10), 50)
    offset = int(args.get("offset") or 0)
    sql = "SELECT * FROM invoices"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY issued_at DESC LIMIT ? OFFSET ?"
    rows = db.query(sql, tuple(params) + (limit, offset))
    total = db.query_one(("SELECT COUNT(*) AS n FROM invoices" + (" WHERE " + " AND ".join(where) if where else "")), tuple(params))["n"]
    return {"invoices": rows, "count": len(rows), "total": total}


def get_invoice(args, ctx):
    _require(args, "invoice_id")
    inv = ctx["db"].query_one("SELECT * FROM invoices WHERE id = ?", (str(args["invoice_id"]).upper(),))
    if not inv:
        raise ToolError(f"Invoice '{args['invoice_id']}' not found. You can list invoices with list_invoices.",
                        code="not_found")
    inv["items"] = ctx["db"].parse_json(inv.pop("items"), [])
    return inv


def send_invoice(args, ctx):
    _require(args, "invoice_id")
    db = ctx["db"]
    inv = db.query_one("SELECT * FROM invoices WHERE id = ?", (str(args["invoice_id"]).upper(),))
    if not inv:
        raise ToolError(f"Invoice '{args['invoice_id']}' not found.", code="not_found")
    if inv["status"] in ("paid", "cancelled"):
        raise ToolError(f"Cannot send invoice in status '{inv['status']}'.")
    db.execute("UPDATE invoices SET status='sent', sent_at=? WHERE id=?",
               (ctx["now"].strftime("%Y-%m-%dT%H:%M:%SZ"), inv["id"]))
    return {"message": f"Invoice {inv['id']} sent to {inv['customer_email']}.",
            "invoice_id": inv["id"], "customer_email": inv["customer_email"], "status": "sent"}


def update_invoice(args, ctx):
    _require(args, "invoice_id")
    db = ctx["db"]
    inv = db.query_one("SELECT * FROM invoices WHERE id = ?", (str(args["invoice_id"]).upper(),))
    if not inv:
        raise ToolError(f"Invoice '{args['invoice_id']}' not found.", code="not_found")
    sets, params = [], []
    if args.get("amount") is not None:
        sets.append("amount = ?"); params.append(round(_num(args, "amount"), 2))
    if args.get("status"):
        sets.append("status = ?"); params.append(args["status"])
    if args.get("due_date"):
        sets.append("due_at = ?"); params.append(args["due_date"])
    if not sets:
        raise ToolError("Nothing to update: provide amount, status or due_date.", code="invalid_parameter")
    params.append(inv["id"])
    db.execute(f"UPDATE invoices SET {', '.join(sets)} WHERE id = ?", tuple(params))
    return get_invoice({"invoice_id": inv["id"]}, ctx)


def cancel_invoice(args, ctx):
    _require(args, "invoice_id")
    db = ctx["db"]
    inv = db.query_one("SELECT * FROM invoices WHERE id = ?", (str(args["invoice_id"]).upper(),))
    if not inv:
        raise ToolError(f"Invoice '{args['invoice_id']}' not found.", code="not_found")
    db.execute("UPDATE invoices SET status='cancelled' WHERE id=?", (inv["id"],))
    return {"message": f"Invoice {inv['id']} cancelled.", "invoice_id": inv["id"], "status": "cancelled"}


def record_invoice_payment(args, ctx):
    _require(args, "invoice_id")
    db = ctx["db"]
    inv = db.query_one("SELECT * FROM invoices WHERE id = ?", (str(args["invoice_id"]).upper(),))
    if not inv:
        raise ToolError(f"Invoice '{args['invoice_id']}' not found.", code="not_found")
    amount = _num(args, "amount", inv["amount"])
    amount = min(amount, inv["amount"])
    now = ctx["now"]
    seq = db.query_one("SELECT COALESCE(MAX(CAST(substr(id, 5) AS INTEGER)), 0) + 1 AS n FROM payments")["n"]
    pay_id = f"PAY-{seq:04d}"
    db.execute(
        "INSERT INTO payments (id, user_id, invoice_id, amount, currency, method, status, created_at)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (pay_id, inv["user_id"], inv["id"], round(amount, 2), inv["currency"],
         args.get("payment_method") or "balance", "succeeded", now.strftime("%Y-%m-%dT%H:%M:%SZ")),
    )
    if amount >= inv["amount"] - 1e-9:
        db.execute("UPDATE invoices SET status='paid', paid_at=? WHERE id=?",
                   (now.strftime("%Y-%m-%dT%H:%M:%SZ"), inv["id"]))
    return {"message": f"Payment {pay_id} of {inv['currency']} {amount:,.2f} recorded against {inv['id']}.",
            "payment_id": pay_id, "invoice_id": inv["id"],
            "invoice_status": "paid" if amount >= inv["amount"] - 1e-9 else inv["status"]}


def get_invoice_summary(args, ctx):
    db = ctx["db"]
    uid = _uid(args) if args.get("user_id") else None
    where = " WHERE user_id = ?" if uid else ""
    params = (uid,) if uid else ()
    by_status = db.query(f"SELECT status, COUNT(*) AS count, ROUND(SUM(amount),2) AS total FROM invoices{where} GROUP BY status", params)
    overall = db.query_one(f"SELECT COUNT(*) AS invoices, ROUND(SUM(CASE WHEN status IN ('sent','overdue') THEN amount ELSE 0 END),2) AS pending_amount FROM invoices{where}", params)
    return {"user_id": uid or "all", "total_invoices": overall["invoices"],
            "pending_amount": overall["pending_amount"], "currency": "USD",
            "by_status": {r["status"]: r["count"] for r in by_status},
            "by_status_total": {r["status"]: r["total"] for r in by_status}}


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

def create_payment(args, ctx):
    _require(args, "amount")
    db = ctx["db"]
    amount = _num(args, "amount")
    if amount is None or amount <= 0:
        raise ToolError("amount must be a positive number.", code="invalid_parameter")
    user_id = _uid(args)
    now = ctx["now"]
    seq = db.query_one("SELECT COALESCE(MAX(CAST(substr(id, 5) AS INTEGER)), 0) + 1 AS n FROM payments")["n"]
    pay_id = f"PAY-{seq:04d}"
    method = args.get("method") or "card"
    db.execute(
        "INSERT INTO payments (id, user_id, invoice_id, amount, currency, method, status, created_at)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (pay_id, user_id, None, round(amount, 2), args.get("currency") or "USD", method,
         "succeeded", now.strftime("%Y-%m-%dT%H:%M:%SZ")),
    )
    db.execute(
        "INSERT INTO transactions (id, user_id, type, amount, currency, created_at) VALUES (?,?,?,?,?,?)",
        (f"TXN-{now.strftime('%Y%m%d%H%M%S%f')}", user_id, "sale", round(amount, 2),
         args.get("currency") or "USD", now.strftime("%Y-%m-%dT%H:%M:%SZ")),
    )
    return {"message": f"Payment {pay_id} of {args.get('currency') or 'USD'} {amount:,.2f} succeeded via {method}.",
            "payment_id": pay_id, "amount": round(amount, 2), "method": method, "status": "succeeded"}


def get_payment(args, ctx):
    _require(args, "payment_id")
    pay = ctx["db"].query_one("SELECT * FROM payments WHERE id = ?", (str(args["payment_id"]).upper(),))
    if not pay:
        raise ToolError(f"Payment '{args['payment_id']}' not found.", code="not_found")
    return pay


def list_payments(args, ctx):
    db = ctx["db"]
    where, params = [], []
    if args.get("user_id"):
        where.append("user_id = ?"); params.append(_uid(args))
    if args.get("status"):
        where.append("status = ?"); params.append(args["status"])
    limit = min(int(args.get("limit") or 10), 50)
    offset = int(args.get("offset") or 0)
    sql = "SELECT * FROM payments"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    rows = db.query(sql, tuple(params) + (limit, offset))
    total = db.query_one(("SELECT COUNT(*) AS n FROM payments" + (" WHERE " + " AND ".join(where) if where else "")), tuple(params))["n"]
    return {"payments": rows, "count": len(rows), "total": total}


def capture_payment(args, ctx):
    _require(args, "payment_id")
    db = ctx["db"]
    pay = db.query_one("SELECT * FROM payments WHERE id = ?", (str(args["payment_id"]).upper(),))
    if not pay:
        raise ToolError(f"Payment '{args['payment_id']}' not found.", code="not_found")
    if pay["status"] != "pending":
        raise ToolError(f"Payment is {pay['status']}; only pending payments can be captured.")
    db.execute("UPDATE payments SET status='succeeded' WHERE id=?", (pay["id"],))
    return {"message": f"Payment {pay['id']} captured.", "payment_id": pay["id"], "status": "succeeded"}


def refund_payment(args, ctx):
    _require(args, "payment_id")
    db = ctx["db"]
    pay = db.query_one("SELECT * FROM payments WHERE id = ?", (str(args["payment_id"]).upper(),))
    if not pay:
        raise ToolError(f"Payment '{args['payment_id']}' not found.", code="not_found")
    if pay["status"] != "succeeded":
        raise ToolError(f"Payment is {pay['status']}; only succeeded payments can be refunded.")
    amount = _num(args, "amount", pay["amount"]) or pay["amount"]
    amount = min(amount, pay["amount"])
    now = ctx["now"]
    db.execute("UPDATE payments SET status='refunded' WHERE id=?", (pay["id"],))
    db.execute(
        "INSERT INTO transactions (id, user_id, type, amount, currency, created_at) VALUES (?,?,?,?,?,?)",
        (f"TXN-{now.strftime('%Y%m%d%H%M%S%f')}", pay["user_id"], "refund", round(amount, 2),
         pay["currency"], now.strftime("%Y-%m-%dT%H:%M:%SZ")),
    )
    return {"message": f"Refunded {pay['currency']} {amount:,.2f} for payment {pay['id']}.",
            "payment_id": pay["id"], "refunded_amount": round(amount, 2), "status": "refunded"}


def void_payment(args, ctx):
    _require(args, "payment_id")
    db = ctx["db"]
    pay = db.query_one("SELECT * FROM payments WHERE id = ?", (str(args["payment_id"]).upper(),))
    if not pay:
        raise ToolError(f"Payment '{args['payment_id']}' not found.", code="not_found")
    if pay["status"] != "pending":
        raise ToolError(f"Payment is {pay['status']}; only pending payments can be voided.")
    db.execute("UPDATE payments SET status='failed' WHERE id=?", (pay["id"],))
    return {"message": f"Payment {pay['id']} voided.", "payment_id": pay["id"], "status": "voided"}


def get_payment_history(args, ctx):
    db = ctx["db"]
    uid = _uid(args)
    limit = min(int(args.get("limit") or 10), 50)
    rows = db.query("SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (uid, limit))
    return {"user_id": uid, "payments": rows, "count": len(rows)}


# ---------------------------------------------------------------------------
# Disputes
# ---------------------------------------------------------------------------

def list_disputes(args, ctx):
    db = ctx["db"]
    where, params = [], []
    if args.get("user_id"):
        where.append("user_id = ?"); params.append(_uid(args))
    if args.get("status"):
        where.append("status = ?"); params.append(args["status"])
    limit = min(int(args.get("limit") or 20), 50)
    sql = "SELECT * FROM disputes"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY opened_at DESC LIMIT ?"
    rows = db.query(sql, tuple(params) + (limit,))
    return {"disputes": rows, "count": len(rows),
            "filter": {"user_id": args.get("user_id"), "status": args.get("status")}}


def get_dispute(args, ctx):
    _require(args, "dispute_id")
    dsp = ctx["db"].query_one("SELECT * FROM disputes WHERE id = ?", (str(args["dispute_id"]).upper(),))
    if not dsp:
        raise ToolError(f"Dispute '{args['dispute_id']}' not found.", code="not_found")
    return dsp


def open_dispute(args, ctx):
    _require(args, "user_id", "reason")
    db = ctx["db"]
    uid = _uid(args)
    now = ctx["now"]
    seq = db.query_one("SELECT COALESCE(MAX(CAST(substr(id, 5) AS INTEGER)), 0) + 1 AS n FROM disputes")["n"]
    dsp_id = f"DSP-{seq:04d}"
    db.execute(
        "INSERT INTO disputes (id, user_id, payment_id, reason, status, opened_at, last_update_at) VALUES (?,?,?,?,?,?,?)",
        (dsp_id, uid, args.get("payment_id"), args["reason"], "open",
         now.strftime("%Y-%m-%dT%H:%M:%SZ"), now.strftime("%Y-%m-%dT%H:%M:%SZ")),
    )
    return {"message": f"Dispute {dsp_id} opened ({args['reason']}).", "dispute_id": dsp_id, "status": "open"}


def respond_to_dispute(args, ctx):
    _require(args, "dispute_id", "message")
    db = ctx["db"]
    dsp = db.query_one("SELECT * FROM disputes WHERE id = ?", (str(args["dispute_id"]).upper(),))
    if not dsp:
        raise ToolError(f"Dispute '{args['dispute_id']}' not found.", code="not_found")
    db.execute("UPDATE disputes SET status='under_review', last_update_at=? WHERE id=?",
               (ctx["now"].strftime("%Y-%m-%dT%H:%M:%SZ"), dsp["id"]))
    return {"message": f"Response submitted for dispute {dsp['id']}; moved to under_review.",
            "dispute_id": dsp["id"], "status": "under_review"}


def accept_dispute(args, ctx):
    _require(args, "dispute_id")
    db = ctx["db"]
    dsp = db.query_one("SELECT * FROM disputes WHERE id = ?", (str(args["dispute_id"]).upper(),))
    if not dsp:
        raise ToolError(f"Dispute '{args['dispute_id']}' not found.", code="not_found")
    db.execute("UPDATE disputes SET status='closed', last_update_at=? WHERE id=?",
               (ctx["now"].strftime("%Y-%m-%dT%H:%M:%SZ"), dsp["id"]))
    return {"message": f"Dispute {dsp['id']} accepted and closed.", "dispute_id": dsp["id"], "status": "closed", "outcome": "accepted"}


def close_dispute(args, ctx):
    _require(args, "dispute_id", "outcome")
    db = ctx["db"]
    dsp = db.query_one("SELECT * FROM disputes WHERE id = ?", (str(args["dispute_id"]).upper(),))
    if not dsp:
        raise ToolError(f"Dispute '{args['dispute_id']}' not found.", code="not_found")
    db.execute("UPDATE disputes SET status='closed', last_update_at=? WHERE id=?",
               (ctx["now"].strftime("%Y-%m-%dT%H:%M:%SZ"), dsp["id"]))
    return {"message": f"Dispute {dsp['id']} closed with outcome '{args['outcome']}'.",
            "dispute_id": dsp["id"], "status": "closed", "outcome": args["outcome"]}


def list_dispute_evidence(args, ctx):
    _require(args, "dispute_id")
    dsp = ctx["db"].query_one("SELECT * FROM disputes WHERE id = ?", (str(args["dispute_id"]).upper(),))
    if not dsp:
        raise ToolError(f"Dispute '{args['dispute_id']}' not found.", code="not_found")
    h = int(hashlib.md5(dsp["id"].encode()).hexdigest()[:6], 16)
    evidence = [
        {"type": "bank_statement", "ref": f"stmt_{h:06x}_01", "uploaded_at": dsp["opened_at"]},
        {"type": "receipt", "ref": f"receipt_{h:06x}", "uploaded_at": dsp["opened_at"]},
    ]
    if dsp["reason"] in ("item_not_received",):
        evidence.append({"type": "tracking", "ref": f"TRK{h:08d}", "status": "in_transit"})
    return {"dispute_id": dsp["id"], "evidence": evidence, "count": len(evidence)}


# ---------------------------------------------------------------------------
# Reports & analytics
# ---------------------------------------------------------------------------

def get_sales_report(args, ctx):
    db, now = ctx["db"], ctx["now"]
    start, end, label = _resolve_period(args.get("period"), now)
    w, wp = _range_where(start, end)
    row = db.query_one(
        f"SELECT COUNT(*) AS n, ROUND(SUM(amount),2) AS total, ROUND(AVG(amount),2) AS avg_sale FROM transactions WHERE type='sale' AND {w}",
        wp,
    )
    return {"period": label, "period_key": args.get("period") or "last_month",
            "total_sales": row["total"] or 0.0, "currency": "USD",
            "transaction_count": row["n"], "avg_sale": row["avg_sale"] or 0.0}


def get_revenue_report(args, ctx):
    db, now = ctx["db"], ctx["now"]
    start, end, label = _resolve_period(args.get("period"), now)
    w, wp = _range_where(start, end)
    sales = db.query_one(f"SELECT COALESCE(SUM(amount),0) AS s FROM transactions WHERE type='sale' AND {w}", wp)
    fees = db.query_one(f"SELECT COALESCE(SUM(amount),0) AS f FROM transactions WHERE type='fee' AND {w}", wp)
    net = round(sales["s"] - fees["f"], 2)
    return {"period": label, "gross_sales": round(sales["s"], 2), "fees": round(fees["f"], 2),
            "net_revenue": net, "currency": "USD"}


def get_refund_report(args, ctx):
    db, now = ctx["db"], ctx["now"]
    start, end, label = _resolve_period(args.get("period"), now)
    w, wp = _range_where(start, end)
    row = db.query_one(f"SELECT COUNT(*) AS n, ROUND(SUM(amount),2) AS total FROM transactions WHERE type='refund' AND {w}", wp)
    dsp = db.query_one(f"SELECT reason, COUNT(*) AS n FROM disputes WHERE opened_at >= ? AND opened_at < ? GROUP BY reason ORDER BY n DESC LIMIT 3", wp)
    return {"period": label, "total_refunds": row["total"] or 0.0, "refund_count": row["n"],
            "currency": "USD", "top_dispute_reasons": [dict(d) for d in dsp] if isinstance(dsp, list) else ([dsp] if dsp else [])}


def get_monthly_summary(args, ctx):
    db, now = ctx["db"], ctx["now"]
    month = args.get("month")
    if month:
        try:
            y, m = int(month[:4]), int(month[5:7])
            start = datetime(y, m, 1)
            end = _month_shift(start.date(), 1)
            label = f"{start.strftime('%B %Y')}"
        except Exception:
            raise ToolError("month must be formatted YYYY-MM.", code="invalid_parameter")
    else:
        start = datetime(now.year, now.month, 1)
        end = _month_shift(now.date(), 1)
        label = start.strftime("%B %Y")
    w, wp = _range_where(start.date(), end)
    out = {"month": label}
    for ttype, key in (("sale", "sales"), ("refund", "refunds"), ("fee", "fees"), ("payout", "payouts")):
        r = db.query_one(f"SELECT COUNT(*) AS n, ROUND(SUM(amount),2) AS total FROM transactions WHERE type=? AND {w}", (ttype, *wp))
        out[key] = r["total"] or 0.0
        out[f"{key}_count"] = r["n"]
    out["net"] = round(out["sales"] - out["fees"], 2)
    out["currency"] = "USD"
    return out


def export_sales_csv(args, ctx):
    db, now = ctx["db"], ctx["now"]
    start, end, label = _resolve_period(args.get("period"), now)
    w, wp = _range_where(start, end)
    rows = db.query(f"SELECT id, user_id, amount, created_at FROM transactions WHERE type='sale' AND {w} ORDER BY created_at DESC LIMIT 50", wp)
    buf = io.StringIO()
    wtr = csv.writer(buf)
    wtr.writerow(["transaction_id", "user_id", "amount_usd", "created_at"])
    for r in rows:
        wtr.writerow([r["id"], r["user_id"], f'{r["amount"]:.2f}', r["created_at"]])
    return {"period": label, "rows_exported": len(rows), "csv": buf.getvalue()}


def get_gmv(args, ctx):
    db, now = ctx["db"], ctx["now"]
    start, end, label = _resolve_period(args.get("period"), now)
    w, wp = _range_where(start, end)
    cur = db.query_one(f"SELECT COALESCE(SUM(amount),0) AS s, COUNT(*) AS n FROM transactions WHERE type='sale' AND {w}", wp)
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - (end - start)
    pw, pp = _range_where(prev_start, prev_end + timedelta(days=1))
    prev = db.query_one(f"SELECT COALESCE(SUM(amount),0) AS s FROM transactions WHERE type='sale' AND {pw}", pp)
    delta = ((cur["s"] - prev["s"]) / prev["s"] * 100) if prev["s"] else None
    return {"period": label, "gmv": round(cur["s"], 2), "transactions": cur["n"], "currency": "USD",
            "previous_period_gmv": round(prev["s"], 2), "period_over_period_pct": round(delta, 1) if delta is not None else None}


def get_top_customers(args, ctx):
    db, now = ctx["db"], ctx["now"]
    start, end, label = _resolve_period(args.get("period"), now)
    w, wp = _range_where(start, end)
    limit = min(int(args.get("limit") or 5), 20)
    rows = db.query(
        f"SELECT t.user_id, u.name, COUNT(*) AS purchases, ROUND(SUM(t.amount),2) AS total FROM transactions t LEFT JOIN users u ON u.id = t.user_id WHERE t.type='sale' AND {w} GROUP BY t.user_id ORDER BY total DESC LIMIT ?",
        wp + (limit,),
    )
    return {"period": label, "top_customers": rows, "currency": "USD"}


def get_channel_breakdown(args, ctx):
    db, now = ctx["db"], ctx["now"]
    start, end, label = _resolve_period(args.get("period"), now)
    w, wp = _range_where(start, end)
    rows = db.query(f"SELECT method, COUNT(*) AS n, ROUND(SUM(amount),2) AS total FROM payments WHERE status='succeeded' AND {w} GROUP BY method ORDER BY total DESC", wp)
    return {"period": label, "channels": rows, "currency": "USD"}


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

def get_customer(args, ctx):
    _require(args, "user_id")
    db = ctx["db"]
    uid = _uid(args)
    u = db.query_one("SELECT * FROM users WHERE id = ?", (uid,))
    if not u:
        raise ToolError(f"Customer '{uid}' not found.", code="not_found")
    u["invoice_count"] = db.query_one("SELECT COUNT(*) AS n FROM invoices WHERE user_id=?", (uid,))["n"]
    u["payment_count"] = db.query_one("SELECT COUNT(*) AS n FROM payments WHERE user_id=?", (uid,))["n"]
    u["open_disputes"] = db.query_one("SELECT COUNT(*) AS n FROM disputes WHERE user_id=? AND status='open'", (uid,))["n"]
    return u


def list_customers(args, ctx):
    db = ctx["db"]
    limit = min(int(args.get("limit") or 10), 50)
    offset = int(args.get("offset") or 0)
    rows = db.query("SELECT * FROM users ORDER BY id LIMIT ? OFFSET ?", (limit, offset))
    total = db.count("users")
    return {"customers": rows, "count": len(rows), "total": total}


def create_customer(args, ctx):
    _require(args, "name", "email")
    db = ctx["db"]
    existing = db.query_one("SELECT id FROM users WHERE email = ?", (str(args["email"]).lower(),))
    if existing:
        return get_customer({"user_id": existing["id"]}, ctx) | {"message": "Customer already exists."}
    seq = db.query_one("SELECT COALESCE(MAX(CAST(substr(id, 6) AS INTEGER)), 350) + 1 AS n FROM users WHERE id LIKE 'user_%'")["n"]
    uid = f"user_{seq}"
    db.execute("INSERT INTO users (id, name, email, country, created_at) VALUES (?,?,?,?,?)",
               (uid, args["name"], str(args["email"]).lower(), args.get("country") or "US",
                ctx["now"].strftime("%Y-%m-%dT%H:%M:%SZ")))
    return get_customer({"user_id": uid}, ctx) | {"message": f"Customer {uid} created."}


def update_customer(args, ctx):
    _require(args, "user_id")
    db = ctx["db"]
    uid = _uid(args)
    if not db.query_one("SELECT id FROM users WHERE id=?", (uid,)):
        raise ToolError(f"Customer '{uid}' not found.", code="not_found")
    sets, params = [], []
    for k in ("name", "email", "country"):
        if args.get(k):
            sets.append(f"{k} = ?"); params.append(args[k])
    if not sets:
        raise ToolError("Nothing to update: provide name, email or country.", code="invalid_parameter")
    params.append(uid)
    db.execute(f"UPDATE users SET {', '.join(sets)} WHERE id = ?", tuple(params))
    return get_customer({"user_id": uid}, ctx)


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------

def list_webhooks(args, ctx):
    db = ctx["db"]
    sql = "SELECT * FROM webhooks"
    if args.get("active_only") == "true":
        sql += " WHERE active = 1"
    rows = db.query(sql + " ORDER BY id")
    for r in rows:
        r["events"] = db.parse_json(r["events"], [])
        r["active"] = bool(r["active"])
    return {"webhooks": rows, "count": len(rows)}


def create_webhook(args, ctx):
    _require(args, "url", "events")
    db = ctx["db"]
    events = [e.strip() for e in str(args["events"]).split(",") if e.strip()]
    seq = db.query_one("SELECT COALESCE(MAX(CAST(substr(id, 5) AS INTEGER)), 0) + 1 AS n FROM webhooks")["n"]
    wh_id = f"WHK-{seq:03d}"
    db.execute("INSERT INTO webhooks (id, url, events, active) VALUES (?,?,?,1)",
               (wh_id, args["url"], str(events)))
    return {"message": f"Webhook {wh_id} created.", "webhook_id": wh_id, "url": args["url"], "events": events}


def test_webhook(args, ctx):
    _require(args, "webhook_id")
    wh = ctx["db"].query_one("SELECT * FROM webhooks WHERE id = ?", (str(args["webhook_id"]).upper(),))
    if not wh:
        raise ToolError(f"Webhook '{args['webhook_id']}' not found.", code="not_found")
    return {"webhook_id": wh["id"], "url": wh["url"], "test_event": "webhook.test",
            "simulated_response": 200, "latency_ms": 42, "status": "delivered (simulated)"}


# ---------------------------------------------------------------------------
# FX
# ---------------------------------------------------------------------------

def _rate(db, base, quote):
    base, quote = base.upper(), quote.upper()
    if base == quote:
        return 1.0
    direct = db.query_one("SELECT rate FROM exchange_rates WHERE base=? AND quote=?", (base, quote))
    if direct:
        return direct["rate"]
    via_usd_b = db.query_one("SELECT rate FROM exchange_rates WHERE base=? AND quote='USD'", (base,))
    via_usd_q = db.query_one("SELECT rate FROM exchange_rates WHERE base='USD' AND quote=?", (quote,))
    if via_usd_b and via_usd_q:
        return round(via_usd_b["rate"] * via_usd_q["rate"], 6)
    raise ToolError(f"No exchange rate available for {base} -> {quote}.", code="not_found")


def get_exchange_rate(args, ctx):
    _require(args, "base", "quote")
    r = _rate(ctx["db"], args["base"], args["quote"])
    return {"base": args["base"].upper(), "quote": args["quote"].upper(), "rate": r,
            "updated_at": ctx["now"].strftime("%Y-%m-%dT%H:%M:%SZ")}


def convert_currency(args, ctx):
    _require(args, "amount", "base", "quote")
    amount = _num(args, "amount")
    r = _rate(ctx["db"], args["base"], args["quote"])
    return {"amount": round(amount, 2), "base": args["base"].upper(), "quote": args["quote"].upper(),
            "rate": r, "converted": round(amount * r, 2)}


def list_currencies(args, ctx):
    rows = ctx["db"].query("SELECT quote, rate FROM exchange_rates WHERE base='USD' ORDER BY quote")
    return {"base": "USD", "currencies": rows}


# ---------------------------------------------------------------------------
# Cards / subscriptions / transfers (synthetic entities)
# ---------------------------------------------------------------------------

def _synth_id(prefix: str, *parts) -> str:
    h = hashlib.md5("|".join(str(p) for p in parts).encode()).hexdigest()[:10]
    return f"{prefix}_{h}"


def tokenize_card(args, ctx):
    _require(args, "brand", "last4")
    uid = _uid(args)
    token = _synth_id("tok", uid, args["brand"], args["last4"])
    return {"user_id": uid, "brand": args["brand"], "last4": args["last4"],
            "token": token, "status": "tokenized",
            "note": "synthetic card token (prototype)"}


def create_card_payment(args, ctx):
    _require(args, "amount", "last4")
    uid = _uid(args)
    amount = round(_num(args, "amount"), 2)
    pay = _synth_id("pi", uid, args["last4"], amount, str(args.get("currency", "USD")))
    return {"payment_intent": pay, "user_id": uid, "amount": amount,
            "currency": (args.get("currency") or "USD").upper(),
            "brand": f"card•••• {args['last4']}", "status": "succeeded",
            "note": "synthetic card charge (prototype)"}


def list_card_payments(args, ctx):
    uid = _uid(args)
    limit = min(int(args.get("limit") or 5), 20)
    rows = ctx["db"].query("SELECT * FROM payments WHERE user_id=? AND method='card' ORDER BY created_at DESC LIMIT ?", (uid, limit))
    return {"user_id": uid, "card_payments": rows, "count": len(rows)}


def create_subscription(args, ctx):
    _require(args, "plan", "amount", "interval")
    uid = _uid(args)
    amount = round(_num(args, "amount"), 2)
    sub = _synth_id("sub", uid, args["plan"], amount, args["interval"])
    return {"subscription_id": sub, "user_id": uid, "plan": args["plan"], "amount": amount,
            "interval": args["interval"], "status": "active",
            "current_period_end": (ctx["now"] + timedelta(days=30 if args["interval"] == "month" else 365)).strftime("%Y-%m-%d"),
            "note": "synthetic subscription (prototype)"}


def list_subscriptions(args, ctx):
    uid = _uid(args)
    subs = [create_subscription({"plan": p, "amount": a, "interval": "month", "user_id": uid}, ctx)
            for p, a in (("pro", 49.0),) if int(hashlib.md5(uid.encode()).hexdigest()[:4], 16) % 3 == 0]
    return {"user_id": uid, "subscriptions": subs, "count": len(subs),
            "note": "synthetic subscription data (prototype)"}


def cancel_subscription(args, ctx):
    _require(args, "subscription_id")
    return {"subscription_id": str(args["subscription_id"]), "status": "canceled",
            "cancellation_effective": (ctx["now"] + timedelta(days=30)).strftime("%Y-%m-%d"),
            "note": "synthetic cancellation (prototype)"}


def get_subscription_usage(args, ctx):
    _require(args, "subscription_id")
    sid = str(args["subscription_id"])
    h = int(hashlib.md5(sid.encode()).hexdigest()[:8], 16)
    return {"subscription_id": sid,
            "usage": [{"metric": "api_calls", "value": h % 90000 + 1000, "limit": 100000},
                      {"metric": "data_processed_gb", "value": (h % 400) / 10.0, "limit": 50.0}],
            "invoices": [f"IN_{(h % 100) + 1:03d}_{m:02d}26" for m in range(max(1, 7 - (h % 6)), 7)],
            "note": "synthetic usage (prototype)"}


def create_transfer(args, ctx):
    _require(args, "amount", "recipient")
    uid = _uid(args)
    amount = round(_num(args, "amount"), 2)
    trf = _synth_id("trf", uid, args["recipient"], amount)
    return {"transfer_id": trf, "user_id": uid, "amount": amount,
            "currency": (args.get("currency") or "USD").upper(), "recipient": args["recipient"],
            "status": "in_transit", "eta": (ctx["now"] + timedelta(days=1)).strftime("%Y-%m-%d"),
            "note": "synthetic transfer (prototype)"}


def get_transfer(args, ctx):
    _require(args, "transfer_id")
    tid = str(args["transfer_id"])
    h = int(hashlib.md5(tid.encode()).hexdigest()[:4], 16)
    status = "in_transit" if h % 3 else "settled"
    return {"transfer_id": tid, "status": status, "note": "synthetic transfer (prototype)"}


def list_transfers(args, ctx):
    uid = _uid(args)
    limit = min(int(args.get("limit") or 5), 20)
    rows = [create_transfer({"amount": 100.0 * (i + 1), "recipient": f"DE893704004405320130{100 + i}", "user_id": uid}, ctx)
            for i in range(min(limit, 3))]
    return {"user_id": uid, "transfers": rows, "count": len(rows),
            "note": "synthetic transfer data (prototype)"}


# ---------------------------------------------------------------------------
# Support
# ---------------------------------------------------------------------------

def create_ticket(args, ctx):
    _require(args, "subject")
    db = ctx["db"]
    uid = _uid(args) if args.get("user_id") else None
    seq = db.query_one("SELECT COALESCE(MAX(CAST(substr(id, 5) AS INTEGER)), 0) + 1 AS n FROM tickets")["n"]
    tid = f"TKT-{seq:04d}"
    db.execute("INSERT INTO tickets (id, user_id, subject, status, priority, created_at) VALUES (?,?,?,?,?,?)",
               (tid, uid, args["subject"], "open", args.get("priority") or "medium",
                ctx["now"].strftime("%Y-%m-%dT%H:%M:%SZ")))
    return {"message": f"Support ticket {tid} created.", "ticket_id": tid, "status": "open"}


def list_tickets(args, ctx):
    db = ctx["db"]
    where, params = [], []
    if args.get("user_id"):
        where.append("user_id = ?"); params.append(_uid(args))
    if args.get("status"):
        where.append("status = ?"); params.append(args["status"])
    limit = min(int(args.get("limit") or 10), 50)
    sql = "SELECT * FROM tickets"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT ?"
    rows = db.query(sql, tuple(params) + (limit,))
    return {"tickets": rows, "count": len(rows)}


def get_ticket(args, ctx):
    _require(args, "ticket_id")
    t = ctx["db"].query_one("SELECT * FROM tickets WHERE id = ?", (str(args["ticket_id"]).upper(),))
    if not t:
        raise ToolError(f"Ticket '{args['ticket_id']}' not found.", code="not_found")
    return t


def close_ticket(args, ctx):
    _require(args, "ticket_id")
    db = ctx["db"]
    t = db.query_one("SELECT * FROM tickets WHERE id = ?", (str(args["ticket_id"]).upper(),))
    if not t:
        raise ToolError(f"Ticket '{args['ticket_id']}' not found.", code="not_found")
    db.execute("UPDATE tickets SET status='closed' WHERE id=?", (t["id"],))
    return {"message": f"Ticket {t['id']} closed.", "ticket_id": t["id"], "status": "closed"}


# ---------------------------------------------------------------------------
# Fraud
# ---------------------------------------------------------------------------

def score_transaction(args, ctx):
    _require(args, "amount")
    amount = _num(args, "amount")
    seed = f"{amount}|{args.get('country', '')}|{args.get('user_id', '')}"
    h = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    score = (h % 1000) / 1000.0
    level = "low" if score < 0.33 else "medium" if score < 0.66 else "high"
    factors = []
    if amount and amount > 5000:
        factors.append("high_amount")
    if args.get("country") and args["country"].upper() not in ("US", "IN", "GB"):
        factors.append("cross_border")
    if not factors:
        factors.append("behavioral_baseline")
    return {"risk_score": round(score, 3), "risk_level": level, "factors": factors,
            "amount": round(amount, 2), "decision": "allow" if level != "high" else "review"}


def list_flagged_transactions(args, ctx):
    db = ctx["db"]
    limit = min(int(args.get("limit") or 5), 20)
    rows = db.query("SELECT * FROM transactions WHERE type='sale' ORDER BY amount DESC LIMIT ?", (limit,))
    return {"flagged_transactions": rows, "count": len(rows),
            "note": "top-amount heuristic stand-in for the real fraud queue"}


# ---------------------------------------------------------------------------
# dispatch table
# ---------------------------------------------------------------------------

HANDLERS: Dict[str, Callable] = {
    "create_invoice": create_invoice, "list_invoices": list_invoices, "get_invoice": get_invoice,
    "send_invoice": send_invoice, "update_invoice": update_invoice, "cancel_invoice": cancel_invoice,
    "record_invoice_payment": record_invoice_payment, "get_invoice_summary": get_invoice_summary,
    "create_payment": create_payment, "get_payment": get_payment, "list_payments": list_payments,
    "capture_payment": capture_payment, "refund_payment": refund_payment, "void_payment": void_payment,
    "get_payment_history": get_payment_history,
    "list_disputes": list_disputes, "get_dispute": get_dispute, "open_dispute": open_dispute,
    "respond_to_dispute": respond_to_dispute, "accept_dispute": accept_dispute,
    "close_dispute": close_dispute, "list_dispute_evidence": list_dispute_evidence,
    "get_sales_report": get_sales_report, "get_revenue_report": get_revenue_report,
    "get_refund_report": get_refund_report, "get_monthly_summary": get_monthly_summary,
    "export_sales_csv": export_sales_csv, "get_gmv": get_gmv, "get_top_customers": get_top_customers,
    "get_channel_breakdown": get_channel_breakdown,
    "get_customer": get_customer, "list_customers": list_customers,
    "create_customer": create_customer, "update_customer": update_customer,
    "list_webhooks": list_webhooks, "create_webhook": create_webhook, "test_webhook": test_webhook,
    "get_exchange_rate": get_exchange_rate, "convert_currency": convert_currency,
    "list_currencies": list_currencies,
    "tokenize_card": tokenize_card, "create_card_payment": create_card_payment,
    "list_card_payments": list_card_payments,
    "create_subscription": create_subscription, "list_subscriptions": list_subscriptions,
    "cancel_subscription": cancel_subscription, "get_subscription_usage": get_subscription_usage,
    "create_transfer": create_transfer, "get_transfer": get_transfer, "list_transfers": list_transfers,
    "create_ticket": create_ticket, "list_tickets": list_tickets,
    "get_ticket": get_ticket, "close_ticket": close_ticket,
    "score_transaction": score_transaction, "list_flagged_transactions": list_flagged_transactions,
}


def dispatch(handler_key: str, args: Dict, ctx: Dict) -> Any:
    key = handler_key.split(":", 1)[1]
    if key not in HANDLERS:
        raise ToolError(f"No implementation registered for handler '{handler_key}'.", code="not_implemented")
    return HANDLERS[key](args, ctx)
