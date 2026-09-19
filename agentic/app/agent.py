import json, re
from .tools import create_invoice, send_payment, cancel_invoice, invoice_status, dispute_status, sales_report
from .rag import search_knowledge
from .system_search import search_system


def extract_invoice_id(text):
    m = re.search(r"INV-[A-Z0-9]+", text.upper())
    return m.group(0) if m else None


def route(message):
    q = message.lower()
    iid = extract_invoice_id(message)

    if any(x in q for x in ["create invoice", "new invoice", "make invoice"]):
        nums = re.findall(r"(?:₹|rs\.?|inr\s*)?\s*([0-9]+(?:\.[0-9]+)?)", q)
        if not nums:
            return {"type": "action", "tool": "create_invoice", "error": "Please provide the invoice amount."}
        m = re.search(r"(?:for|customer)\s+([A-Za-z][A-Za-z0-9 &._-]+?)(?:\s+(?:for|amount)|\s*$)", message, re.I)
        return {"type": "action", "tool": "create_invoice",
                "args": {"customer": m.group(1).strip() if m else "Unknown Customer",
                         "amount": float(nums[-1]), "currency": "INR"}}

    if any(x in q for x in ["send payment", "make payment", "pay invoice"]) and iid:
        return {"type": "action", "tool": "send_payment", "args": {"invoice_id": iid}}
    if "cancel" in q and "invoice" in q and iid:
        return {"type": "action", "tool": "cancel_invoice", "args": {"invoice_id": iid}}
    if iid and ("invoice status" in q or "status of invoice" in q or "check invoice" in q
                or re.search(r"invoice\s+" + re.escape(iid.lower()) + r"\s+status", q)
                or re.search(r"status\s+of\s+" + re.escape(iid.lower()), q)):
        return {"type": "action", "tool": "invoice_status", "args": {"invoice_id": iid}}
    if "dispute" in q and iid:
        return {"type": "action", "tool": "dispute_status", "args": {"invoice_id": iid}}
    if "sales report" in q or "sales summary" in q:
        return {"type": "action", "tool": "sales_report", "args": {}}
    if iid:
        return {"type": "system_search", "query": iid}
    return {"type": "knowledge_and_gemini", "query": message}


def execute(message):
    d = route(message)
    if d["type"] == "action":
        if "error" in d:
            return d
        fn = {"create_invoice": create_invoice, "send_payment": send_payment,
              "cancel_invoice": cancel_invoice, "invoice_status": invoice_status,
              "dispute_status": dispute_status, "sales_report": sales_report}[d["tool"]]
        return {"type": "action_result", "tool": d["tool"], "result": fn(**d["args"])}
    if d["type"] == "system_search":
        return search_system(d["query"])
    if d["type"] == "knowledge_and_gemini":
        return {"type": "knowledge_context", "source": "KNOWLEDGE_AND_GEMINI",
                "query": d["query"], "results": search_knowledge(d["query"]).get("results", [])}
    return d


def natural_response(result):
    if result.get("type") == "action_result":
        r = result["result"]
        if not r.get("success"): return r["error"]
        t = result["tool"]
        if t == "create_invoice": return f"Invoice {r['invoice_id']} created for {r['customer']} for {r['currency']} {r['amount']:.2f}."
        if t == "send_payment": return f"Payment {r['payment_id']} of {r['amount']:.2f} for {r['invoice_id']} was completed."
        if t == "cancel_invoice": return f"Invoice {r['invoice_id']} has been cancelled."
        if t == "invoice_status":
            x = r["invoice"]; return f"Invoice {x['invoice_id']} is {x['status']} for {x['currency']} {x['amount']:.2f}."
        if t == "dispute_status": return f"Dispute status for {r['invoice_id']}: {r['status']}."
        if t == "sales_report":
            x = r["report"]; return f"Sales report: {x['invoice_count']} invoices, {x['invoiced_amount']:.2f} invoiced, {x['paid_amount']:.2f} paid."
    if result.get("source") == "SYSTEM_SEARCH":
        rows = result.get("results", [])
        if not rows: return "No matching system records found."
        if len(rows) == 1:
            x = rows[0]; return f"{x['invoice_id']} is {x['status']} for {x['customer']} — {x['currency']} {x['amount']:.2f}."
        return f"I found {len(rows)} matching invoice records."
    if result.get("type") == "knowledge_context":
        if result.get("results"):
            return "I found relevant company knowledge, but Gemini is currently unavailable to generate the response."
        return "Gemini is currently unavailable. I can answer general questions when the Gemini service is configured and reachable."
    return "I could not process that request."


def chat(message, history=None):
    result = execute(message)
    fallback = natural_response(result)

    try:
        from .gemini import generate
        context = ""
        if result.get("type") == "action_result":
            context = json.dumps(result, ensure_ascii=False)
        elif result.get("source") == "SYSTEM_SEARCH":
            context = json.dumps(result, ensure_ascii=False)
        elif result.get("type") == "knowledge_context":
            context = json.dumps({"knowledge_results": result.get("results", [])}, ensure_ascii=False)
        ai = generate(message, history=history, context=context)
        if ai:
            return {"message": ai.strip(), "details": result}
    except Exception as exc:
        result = dict(result)
        result["gemini_error"] = str(exc)

    return {"message": fallback, "details": result}
