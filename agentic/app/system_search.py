from .db import connect

def search_system(query):
    q = query.lower().strip()
    with connect() as con:
        if q.startswith("inv-"):
            rows = con.execute("SELECT * FROM invoices WHERE lower(invoice_id)=?", (q,)).fetchall()
        else:
            rows = con.execute(
                "SELECT * FROM invoices WHERE lower(customer) LIKE ? ORDER BY created_at DESC LIMIT 10",
                (f"%{q}%",)
            ).fetchall()
    return {"source": "SYSTEM_SEARCH", "results": [dict(r) for r in rows]}
