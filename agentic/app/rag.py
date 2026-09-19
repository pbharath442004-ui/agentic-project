KNOWLEDGE = [
    ("invoice", "An invoice records the customer, amount, currency, date, and payment status."),
    ("payment", "A payment records an amount paid against an invoice. A full payment marks the invoice PAID."),
    ("cancel", "An OPEN or partially paid invoice can be cancelled by the prototype. Paid invoices cannot be cancelled."),
    ("dispute", "A dispute is a separate record associated with an invoice. The prototype reports the latest dispute.")
]

def search_knowledge(query):
    q = query.lower()
    hits = [text for key, text in KNOWLEDGE if key in q]
    return {"source": "RAG", "results": hits[:3]}
