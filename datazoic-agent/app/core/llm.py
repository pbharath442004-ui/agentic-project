"""LLM layer with two interchangeable backends.

* `OpenAICompatLLM` — calls any OpenAI-compatible /chat/completions endpoint
  with native function calling. This is the "real" path when LLM_API_KEY
  (or OPENAI_API_KEY) is configured.
* `HeuristicLLM` — a deterministic offline planner (rule-based intent
  extraction + regex slot filling + keyword scoring). It implements the
  SAME interface so the whole pipeline — router, executor, memory,
  observability — runs with zero external dependencies, which keeps the
  prototype CI-safe and the demo reproducible.

The interface:
    plan(message, tool_specs, session)   -> LLMResult   (pick tool(s) or answer)
    observe(message, tool_specs, session, observations) -> LLMResult  (final answer or next tools)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from ..config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_PROVIDER, LLM_TIMEOUT_S

SYSTEM_PROMPT = """You are the Datazoic Pay agentic assistant.
You complete business operations by calling the available tools: invoices, payments, disputes,
reports, customers, webhooks, FX, cards, subscriptions, transfers, support and more, plus a
knowledge-base (RAG) tool and system self-query tools.
Rules:
1. Prefer calling a tool over guessing data. Never invent IDs, amounts or statuses.
2. If the user asks a knowledge/policy/how-to question, call system.ask_knowledge_base.
3. If the user asks what capabilities exist or about your last request, use the system tools.
4. If required parameters are missing, ask the user for them — do not invent values.
5. After tool results, answer concisely with the concrete numbers/IDs from the results.
6. For knowledge answers, cite the knowledge-base entries you used."""


@dataclass
class ToolCall:
    name: str
    args: Dict[str, Any] = field(default_factory=dict)
    # arg_refs: {"invoice_id": "result:0.invoice_id"} resolved after prior calls
    arg_refs: Dict[str, str] = field(default_factory=dict)


@dataclass
class LLMResult:
    tool_calls: Optional[List[ToolCall]] = None
    content: Optional[str] = None
    provider: str = ""


# ---------------------------------------------------------------------------
# shared regexes / helpers
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
USER_RE = re.compile(r"\buser[_-]?(\d+)\b", re.I)
AMOUNT_RE = re.compile(r"(?:\$|USD\s?)?\s?(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)\b")
ID_RES = {
    "invoice_id": re.compile(r"\bINV-\d+\b", re.I),
    "payment_id": re.compile(r"\bPAY-\d+\b", re.I),
    "dispute_id": re.compile(r"\bDSP-\d+\b", re.I),
    "ticket_id": re.compile(r"\bTKT-\d+\b", re.I),
    "transfer_id": re.compile(r"\bTRF-\d+\b", re.I),
    "webhook_id": re.compile(r"\bWHK-\d+\b", re.I),
}
PERIOD_WORDS = {
    "last month": "last_month", "previous month": "last_month", "last_month": "last_month",
    "this month": "this_month", "current month": "this_month",
    "yesterday": "last_7_days", "last week": "last_7_days", "past week": "last_7_days",
    "last 30 days": "last_30_days", "past 30 days": "last_30_days", "last month ": "last_month",
    "last 90 days": "last_90_days", "quarter": "last_90_days", "q1": "ytd", "ytd": "ytd",
    "year to date": "ytd", "all time": "all_time", "lifetime": "all_time",
}
STATUS_WORDS = {
    "open": "open", "paid": "paid", "sent": "sent", "draft": "draft", "overdue": "overdue",
    "cancelled": "cancelled", "canceled": "cancelled", "refunded": "refunded",
    "pending": "pending", "failed": "failed", "closed": "closed",
    "under review": "under_review", "succeeded": "succeeded", "success": "succeeded",
}
MONEY_KEYS = re.compile(r"(amount|total|sales?|revenue|gmv|fee|price|balance|volume|net|cost|converted|avg)", re.I)


def extract_amount(text: str) -> Optional[float]:
    m = AMOUNT_RE.search(text)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def extract_period(text: str) -> Optional[str]:
    low = " " + text.lower() + " "
    for phrase, key in PERIOD_WORDS.items():
        if phrase.strip() in low:
            return key
    return None


def extract_status(text: str) -> Optional[str]:
    low = " " + text.lower() + " "
    for phrase, val in STATUS_WORDS.items():
        if f" {phrase} " in low or low.rstrip().endswith(f" {phrase}"):
            return val
    return None


def extract_id(text: str, key: str) -> Optional[str]:
    m = ID_RES[key].search(text)
    return m.group(0).upper() if m else None


def extract_email(text: str) -> Optional[str]:
    m = EMAIL_RE.search(text)
    return m.group(0) if m else None


def extract_user(text: str) -> Optional[str]:
    m = USER_RE.search(text)
    return f"user_{m.group(1)}" if m else None


def _title(s: str) -> str:
    return s.replace("_", " ").capitalize()


# ---------------------------------------------------------------------------
# intent classification (drives the heuristic planner)
# ---------------------------------------------------------------------------

META_TOOL_PAT = re.compile(
    r"\bwhat tools?\b|\bavailable (tools|features|capabilities)\b|\bcapabilities\b|\bwhat can you do\b|\bfeature list\b")
META_LAST_PAT = re.compile(r"my last request|last request|status of my last|what did you (do|run)|last (tool )?call")
STRONG_INFO_PAT = re.compile(
    r"\b(how long|how much|how many|why|explain|guide|guides|documentation|docs|policy|policies|"
    r"compliance|kyc|sla|onboarding|procedure|deadline|process|best practice)\b")
CURRENCY_PAT = re.compile(r"\b(USD|EUR|GBP|INR|SGD|AUD|CAD|JPY|MXN|AED)\b")
DOMAIN_NOUN_PAT = re.compile(
    r"\b(invoices?|payments?|disputes?|refunds?|sales|revenue|reports?|gmv|transfers?|webhooks?|"
    r"tickets?|subscriptions?|customers?|balances?|exchange rates?|conversions?|payouts?|channels?|fees?)\b")
ACTION_VERB_PAT = re.compile(
    r"\b(create|send|issue|make|open|cancel|close|refund|capture|void|list|show|get|check|convert|"
    r"calculate|export|approve|respond|reply|test|verify|score|run|pause|resume|rotate|delete|"
    r"update|configure|add|remove|track|view|see|find|submit|pay|charge|set up)\b")
EXIST_PAT = re.compile(r"\b(is there|are there|do i have|do we have|any open|any pending)\b")


def classify_intent(message: str) -> str:
    """Return one of: system_meta_tool | system_meta_last | knowledge | domain | other."""
    low = message.lower()
    if META_TOOL_PAT.search(low):
        return "system_meta_tool"
    if META_LAST_PAT.search(low):
        return "system_meta_last"
    if any(extract_id(message, k) for k in ID_RES):
        return "domain"
    if STRONG_INFO_PAT.search(low):
        return "knowledge"
    if len(CURRENCY_PAT.findall(message)) >= 2 or "exchange rate" in low or "convert" in low:
        return "domain"
    if DOMAIN_NOUN_PAT.search(low) and (
        ACTION_VERB_PAT.search(low) or EXIST_PAT.search(low)
        or extract_amount(message) is not None or extract_user(message)
        or extract_period(message) or extract_status(message)
    ):
        return "domain"
    if low.rstrip().endswith("?") and not DOMAIN_NOUN_PAT.search(low):
        return "knowledge"
    return "other"


# ---------------------------------------------------------------------------
# Heuristic (offline deterministic) planner
# ---------------------------------------------------------------------------

class HeuristicLLM:
    name = "heuristic"

    def __init__(self):
        self.provider = "heuristic (deterministic offline planner)"

    # ---- planning ---------------------------------------------------------
    def plan(self, message: str, tool_specs: List[Dict], session: Dict) -> LLMResult:
        names = {t["function"]["name"] for t in tool_specs}

        def has(*ns):
            return any(n in names for n in ns)

        low = message.lower()
        intent = classify_intent(message)

        # 1) system self-queries (most explicit signals)
        if intent == "system_meta_tool" and has("system.search_capabilities"):
            return LLMResult(tool_calls=[ToolCall("system.search_capabilities", {"query": message.strip()})],
                             provider=self.provider)
        if intent == "system_meta_last" and has("system.get_last_request"):
            return LLMResult(tool_calls=[ToolCall("system.get_last_request", {})], provider=self.provider)

        # 2) knowledge / how-to / policy questions -> RAG tool
        if intent == "knowledge" and has("system.ask_knowledge_base"):
            return LLMResult(tool_calls=[ToolCall("system.ask_knowledge_base", {"query": message.strip()})],
                             provider=self.provider)

        email = extract_email(message)
        amount = extract_amount(message)
        user = extract_user(message)
        period = extract_period(message)
        status = extract_status(message)

        # 3) "send an invoice for $50 to john@example.com" -> create + send chain
        if re.search(r"\b(send|issue|create|make)\b", low) and "invoice" in low and has("paypal.invoices.create_invoice"):
            if email and has("paypal.invoices.send_invoice") and re.search(r"\bsend\b", low):
                args = {"customer_email": email}
                if amount is not None:
                    args["amount"] = amount
                return LLMResult(tool_calls=[
                    ToolCall("paypal.invoices.create_invoice", args,
                             arg_refs={}),
                    ToolCall("paypal.invoices.send_invoice", {},
                             arg_refs={"invoice_id": "result:0.id"}),
                ], provider=self.provider)
            args = {}
            if email:
                args["customer_email"] = email
            if amount is not None:
                args["amount"] = amount
            if user:
                args["user_id"] = user
            if re.search(r"\b(consulting|services|subscription|license|support)\b", low):
                args["description"] = re.search(r"\b(consulting|services|subscription|license|support)[^,]*\b", low).group(0).strip().title()
            return LLMResult(tool_calls=[ToolCall("paypal.invoices.create_invoice", args)],
                             provider=self.provider)

        # 4) disputes
        if "dispute" in low and has("paypal.disputes.list_disputes"):
            args = {}
            if user:
                args["user_id"] = user
            if status:
                args["status"] = status
            if re.search(r"\b(any|is there|are there|open)\b", low) and status is None:
                args["status"] = "open"
            return LLMResult(tool_calls=[ToolCall("paypal.disputes.list_disputes", args)], provider=self.provider)
        if re.search(r"\bopen (a |an )?dispute\b", low) and has("paypal.disputes.open_dispute"):
            args = {"user_id": user or "user_123"}
            m = re.search(r"\b(unauthorized|not received|duplicate|defective|not as described)\b", low)
            if m:
                args["reason"] = {"unauthorized": "unauthorized_transaction", "not received": "item_not_received",
                                  "duplicate": "duplicate_charge", "defective": "defective_product",
                                  "not as described": "not_as_described"}[m.group(1)]
            else:
                args["reason"] = "other"
            pid = extract_id(message, "payment_id")
            if pid:
                args["payment_id"] = pid
            return LLMResult(tool_calls=[ToolCall("paypal.disputes.open_dispute", args)], provider=self.provider)
        dsp_id = extract_id(message, "dispute_id")
        if dsp_id and has("paypal.disputes.get_dispute"):
            if re.search(r"\b(respond|reply)\b", low) and has("paypal.disputes.respond_to_dispute"):
                return LLMResult(tool_calls=[ToolCall("paypal.disputes.respond_to_dispute",
                                                      {"dispute_id": dsp_id, "message": "Response submitted by the agent on behalf of the merchant."})],
                                 provider=self.provider)
            if re.search(r"\bclose\b", low) and has("paypal.disputes.close_dispute"):
                return LLMResult(tool_calls=[ToolCall("paypal.disputes.close_dispute",
                                                      {"dispute_id": dsp_id, "outcome": status if status in ("won", "lost", "accepted") else "closed" if status else "won"})],
                                 provider=self.provider)
            return LLMResult(tool_calls=[ToolCall("paypal.disputes.get_dispute", {"dispute_id": dsp_id})],
                             provider=self.provider)

        # 5) reports / metrics
        if re.search(r"\b(sales volume|total sales|gmv|revenue|sales report|refund report|monthly summary|top customers|channel breakdown)\b", low):
            if "revenue" in low and has("paypal.reports.get_revenue_report"):
                tc = ToolCall("paypal.reports.get_revenue_report", {"period": period or "last_month"})
                return LLMResult(tool_calls=[tc], provider=self.provider)
            if "refund" in low and has("paypal.reports.get_refund_report"):
                return LLMResult(tool_calls=[ToolCall("paypal.reports.get_refund_report", {"period": period or "last_month"})],
                                 provider=self.provider)
            if re.search(r"\bmonthly summary\b", low) and has("paypal.reports.get_monthly_summary"):
                m = re.search(r"\b(\d{4}-\d{2})\b", message)
                args = {"month": m.group(1)} if m else {}
                return LLMResult(tool_calls=[ToolCall("paypal.reports.get_monthly_summary", args)], provider=self.provider)
            if re.search(r"\btop customers?\b", low) and has("analytics.metrics.get_top_customers"):
                return LLMResult(tool_calls=[ToolCall("analytics.metrics.get_top_customers", {"period": period or "last_month"})],
                                 provider=self.provider)
            if re.search(r"\bchannel\b", low) and has("analytics.metrics.get_channel_breakdown"):
                return LLMResult(tool_calls=[ToolCall("analytics.metrics.get_channel_breakdown", {"period": period or "last_month"})],
                                 provider=self.provider)
            if has("paypal.reports.get_sales_report"):
                return LLMResult(tool_calls=[ToolCall("paypal.reports.get_sales_report", {"period": period or "last_month"})],
                                 provider=self.provider)

        # 6) payments
        if re.search(r"\b(send|make|create|process)\b", low) and re.search(r"\b(payment|pay)\b", low) and not "invoice" in low and has("paypal.payments.create_payment"):
            args = {"amount": amount} if amount is not None else {}
            m = re.search(r"\b(card|bank|wallet|balance)\b", low)
            if m:
                args["method"] = m.group(1) if m.group(1) != "bank" else "bank_transfer"
            if user:
                args["user_id"] = user
            c = re.search(r"\b(USD|EUR|GBP|INR|SGD)\b", message, re.I)
            if c:
                args["currency"] = c.group(1).upper()
            return LLMResult(tool_calls=[ToolCall("paypal.payments.create_payment", args)], provider=self.provider)
        if re.search(r"\brefund\b", low) and has("paypal.payments.refund_payment"):
            pid = extract_id(message, "payment_id")
            args = {"payment_id": pid} if pid else {}
            if amount is not None:
                args["amount"] = amount
            return LLMResult(tool_calls=[ToolCall("paypal.payments.refund_payment", args)], provider=self.provider)
        pay_id = extract_id(message, "payment_id")
        if pay_id and has("paypal.payments.get_payment"):
            if re.search(r"\brefund\b", low):
                return LLMResult(tool_calls=[ToolCall("paypal.payments.refund_payment", {"payment_id": pay_id})], provider=self.provider)
            if re.search(r"\bcapture\b", low) and has("paypal.payments.capture_payment"):
                return LLMResult(tool_calls=[ToolCall("paypal.payments.capture_payment", {"payment_id": pay_id})], provider=self.provider)
            if re.search(r"\bvoid\b", low) and has("paypal.payments.void_payment"):
                return LLMResult(tool_calls=[ToolCall("paypal.payments.void_payment", {"payment_id": pay_id})], provider=self.provider)
            return LLMResult(tool_calls=[ToolCall("paypal.payments.get_payment", {"payment_id": pay_id})], provider=self.provider)
        if re.search(r"\b(payment (history|list)|list .* payments|my payments)\b", low) and has("paypal.payments.get_payment_history"):
            args = {}
            if user:
                args["user_id"] = user
            return LLMResult(tool_calls=[ToolCall("paypal.payments.get_payment_history", args)], provider=self.provider)
        if re.search(r"\bpayments?\b", low) and has("paypal.payments.list_payments"):
            args = {}
            if user:
                args["user_id"] = user
            if status:
                args["status"] = status
            return LLMResult(tool_calls=[ToolCall("paypal.payments.list_payments", args)], provider=self.provider)

        # 7) invoices (lookups / actions on existing)
        inv_id = extract_id(message, "invoice_id")
        if re.search(r"\bcancel\b", low) and "invoice" in low and has("paypal.invoices.cancel_invoice"):
            args = {"invoice_id": inv_id} if inv_id else {}
            return LLMResult(tool_calls=[ToolCall("paypal.invoices.cancel_invoice", args)], provider=self.provider)
        if inv_id:
            if re.search(r"\bcancel\b", low) and has("paypal.invoices.cancel_invoice"):
                return LLMResult(tool_calls=[ToolCall("paypal.invoices.cancel_invoice", {"invoice_id": inv_id})], provider=self.provider)
            if re.search(r"\bsend\b", low) and has("paypal.invoices.send_invoice"):
                return LLMResult(tool_calls=[ToolCall("paypal.invoices.send_invoice", {"invoice_id": inv_id})], provider=self.provider)
            if re.search(r"\bsummary\b", low) and has("paypal.invoices.get_invoice_summary"):
                return LLMResult(tool_calls=[ToolCall("paypal.invoices.get_invoice_summary", {})], provider=self.provider)
            return LLMResult(tool_calls=[ToolCall("paypal.invoices.get_invoice", {"invoice_id": inv_id})], provider=self.provider)
        if re.search(r"\binvoices?\b", low):
            if re.search(r"\bsummary|totals?\b", low) and has("paypal.invoices.get_invoice_summary"):
                args = {}
                if user:
                    args["user_id"] = user
                return LLMResult(tool_calls=[ToolCall("paypal.invoices.get_invoice_summary", args)], provider=self.provider)
            if has("paypal.invoices.list_invoices"):
                args = {}
                if user:
                    args["user_id"] = user
                if status:
                    args["status"] = status
                return LLMResult(tool_calls=[ToolCall("paypal.invoices.list_invoices", args)], provider=self.provider)

        # 8) customers
        if re.search(r"\b(customers?|client|account)\b", low) and "invoice" not in low:
            if user and has("paypal.customers.get_customer"):
                return LLMResult(tool_calls=[ToolCall("paypal.customers.get_customer", {"user_id": user})], provider=self.provider)
            if has("paypal.customers.list_customers"):
                return LLMResult(tool_calls=[ToolCall("paypal.customers.list_customers", {})], provider=self.provider)

        # 9) webhooks
        if "webhook" in low:
            wh_id = extract_id(message, "webhook_id")
            if wh_id and re.search(r"\btest\b", low) and has("paypal.webhooks.test_webhook"):
                return LLMResult(tool_calls=[ToolCall("paypal.webhooks.test_webhook", {"webhook_id": wh_id})], provider=self.provider)
            if re.search(r"\b(create|add|register|new)\b", low) and has("paypal.webhooks.create_webhook"):
                url = re.search(r"https?://\S+", message)
                return LLMResult(tool_calls=[ToolCall("paypal.webhooks.create_webhook",
                                                      {"url": url.group(0) if url else "https://hooks.example.com/datazoic",
                                                       "events": "invoice.paid,payment.captured"})], provider=self.provider)
            if has("paypal.webhooks.list_webhooks"):
                return LLMResult(tool_calls=[ToolCall("paypal.webhooks.list_webhooks", {})], provider=self.provider)

        # 10) FX
        if re.search(r"\b(exchange rate|convert|currency|usd|eur|inr|gbp|sgd)\b", low) and re.search(r"\b(rate|convert)\b", low):
            m = re.search(r"\b(USD|EUR|GBP|INR|SGD|AUD|CAD|JPY)\b", message, re.I)
            m2 = re.search(r"(?:to|into|->)\s*(USD|EUR|GBP|INR|SGD|AUD|CAD|JPY)\b", message, re.I)
            base = (m.group(1) if m else "USD").upper()
            quote = (m2.group(1) if m2 else "USD").upper()
            if amount is not None and has("paypal.fx.convert_currency"):
                return LLMResult(tool_calls=[ToolCall("paypal.fx.convert_currency",
                                                      {"amount": amount, "base": base, "quote": quote})], provider=self.provider)
            if has("paypal.fx.get_exchange_rate"):
                return LLMResult(tool_calls=[ToolCall("paypal.fx.get_exchange_rate",
                                                      {"base": base, "quote": quote if quote != base else "INR"})],
                                 provider=self.provider)

        # 11) tickets
        if re.search(r"\b(ticket|support)\b", low) and has("support.tickets.create_ticket"):
            m = re.search(r"\b(?:about|re:|for)\s+(.{4,60})$", low)
            args = {"subject": m.group(1).strip() if m else message.strip()[:60]}
            if user:
                args["user_id"] = user
            return LLMResult(tool_calls=[ToolCall("support.tickets.create_ticket", args)], provider=self.provider)

        # 12) subscriptions / transfers
        if "subscription" in low and has("stripe.subscriptions.list_subscriptions"):
            if re.search(r"\b(cancel|stop|end)\b", low) and has("stripe.subscriptions.cancel_subscription"):
                return LLMResult(tool_calls=[ToolCall("stripe.subscriptions.cancel_subscription",
                                                      {"subscription_id": "sub_current"})], provider=self.provider)
            args = {}
            if user:
                args["user_id"] = user
            return LLMResult(tool_calls=[ToolCall("stripe.subscriptions.list_subscriptions", args)], provider=self.provider)
        if re.search(r"\btransfer\b", low) and "bank" not in low and has("banking.transfers.create_transfer"):
            return LLMResult(tool_calls=[ToolCall("banking.transfers.create_transfer",
                                                  {"amount": amount} if amount is not None else {})], provider=self.provider)

        # 13) generic scoring over provided tools
        best = self._score_tools(message, tool_specs)
        if best is not None:
            return LLMResult(tool_calls=[ToolCall(best[0], self._generic_args(message, best[0], tool_specs))],
                             provider=self.provider)

        # 14) fallback: answer directly
        return LLMResult(content=(
            "I can help with invoices, payments, disputes, sales reports, customers, webhooks, "
            "exchange rates, subscriptions, transfers and support — or answer questions from the "
            "Datazoic knowledge base. For example: \"send an invoice for $50 to john@example.com\", "
            "\"what was my total sales volume last month?\" or \"what tools are available for managing invoices?\""),
            provider=self.provider)

    # ---- observation -> final answer ----------------------------------------
    def observe(self, message: str, tool_specs: List[Dict], session: Dict,
                observations: List[Dict]) -> LLMResult:
        # normalize: observations carry ToolResult objects; reduce to plain dicts
        obs = [
            {"tool": o["tool"],
             "ok": bool(o["result"].ok),
             "missing": o["result"].missing_params,
             "error": o["result"].error,
             "data": o["result"].data,
             "simulated": o["result"].simulated}
            for o in observations
        ]

        # missing-params clarification
        for o in obs:
            if not o["ok"] and o["missing"]:
                params = ", ".join(o["missing"])
                return LLMResult(content=(
                    f"I need a bit more information to do that — please provide: **{params}**. "
                    f"(If you're not sure, I can list the relevant records first; e.g. \"list my invoices\".)"),
                    provider=self.provider)
            if not o["ok"]:
                return LLMResult(content=(
                    f"I ran `{o['tool']}` but it failed: {o['error']}\n\n"
                    f"You can retry with different details, or ask me to list the records first."),
                    provider=self.provider)

        # knowledge answer
        rag_obs = [o for o in obs if o["tool"] == "system.ask_knowledge_base" and o["ok"]]
        if rag_obs:
            return LLMResult(content=self._format_knowledge_answer(rag_obs[0]["data"]),
                             provider=self.provider)

        # search capabilities answer
        cap_obs = [o for o in obs if o["tool"] == "system.search_capabilities" and o["ok"]]
        if cap_obs:
            data = cap_obs[0]["data"]
            tools = data.get("tools", []) if isinstance(data, dict) else data
            if tools:
                lines = [f"Here are {len(tools)} matching capabilities:", ""]
                for t in tools[:8]:
                    lines.append(f"- **{t['name']}** ({t.get('domain', '')}): {t.get('description', '')[:110]}")
                lines.append("")
                lines.append("Say the word and I'll run one for you.")
                return LLMResult(content="\n".join(lines), provider=self.provider)

        # last request answer
        last_obs = [o for o in obs if o["tool"] == "system.get_last_request" and o["ok"]]
        if last_obs:
            data = last_obs[0]["data"]
            if data:
                return LLMResult(content=(
                    f"Your most recent request was **{data.get('tool')}** "
                    f"(status: **{'success' if data.get('ok') else 'error'}**, "
                    f"{data.get('ms', 0)} ms, at {data.get('at', 'n/a')}).\n"
                    f"Parameters: `{json.dumps(data.get('args', {}))}`\n"
                    f"Result: {self._compact(data.get('data'))}"),
                    provider=self.provider)
            return LLMResult(content="You haven't run any tool requests in this session yet.", provider=self.provider)

        # default: format the (last meaningful) DB result
        meaningful = [o for o in obs if o["ok"]]
        if not meaningful:
            return LLMResult(content="I couldn't complete that — please share more details.", provider=self.provider)
        o = meaningful[-1]
        return LLMResult(content=self._format_data_answer(o["tool"], o["data"], o["simulated"]),
                         provider=self.provider)

    # ---- internals -----------------------------------------------------------
    def _score_tools(self, message: str, tool_specs: List[Dict]):
        from .router import _dice
        scored = []
        for spec in tool_specs:
            fn = spec["function"]
            text = f"{fn['name']} {fn['description']}"
            s = _dice(message, text)
            if s > 0.05:
                scored.append((fn["name"], s))
        if not scored:
            return None
        scored.sort(key=lambda x: -x[1])
        return scored[0]

    def _generic_args(self, message: str, tool_name: str, tool_specs: List[Dict]) -> Dict:
        args: Dict[str, Any] = {}
        spec = next((t for t in tool_specs if t["function"]["name"] == tool_name), None)
        if not spec:
            return args
        props = spec["function"]["parameters"]["properties"]
        low = message.lower()
        for pname, p in props.items():
            if pname in ("customer_email", "email", "recipient_email") and extract_email(message):
                args[pname] = extract_email(message)
            elif pname in ("user_id",) and extract_user(message):
                args[pname] = extract_user(message)
            elif pname == "amount" and extract_amount(message) is not None:
                args[pname] = extract_amount(message)
            elif pname == "period" and extract_period(message):
                args[pname] = extract_period(message)
            elif pname in ("status",) and extract_status(message):
                args[pname] = extract_status(message)
            elif pname == "currency":
                c = re.search(r"\b(USD|EUR|GBP|INR|SGD)\b", message, re.I)
                if c:
                    args[pname] = c.group(1).upper()
            elif "email" in pname and extract_email(message):
                args[pname] = extract_email(message)
            elif pname in ID_RES and extract_id(message, pname):
                args[pname] = extract_id(message, pname)
            elif pname in ("query",) and "invoice" in low or (pname == "query" and re.search(r"\b(manag|list|use)\b", low)):
                args[pname] = re.sub(r"\b(what|which|are|there|available|tools|features|capabilities|for|the|my|a|an)\b", "", low).strip() or low
            elif pname in ("subject",) and re.search(r"\b(about|re:)\s+", low):
                args[pname] = re.search(r"\b(?:about|re:)\s+(.{4,80})", low).group(1).strip().rstrip("?.")
            elif pname in ("reason",) and re.search(r"\b(unauthorized|not received|duplicate|defective)\b", low):
                args[pname] = {"unauthorized": "unauthorized_transaction", "not received": "item_not_received",
                               "duplicate": "duplicate_charge", "defective": "defective_product"}[
                    re.search(r"\b(unauthorized|not received|duplicate|defective)\b", low).group(1)]
            elif pname in ("base", "quote") and re.search(r"\b(USD|EUR|GBP|INR|SGD|AUD|CAD|JPY)\b", message, re.I):
                cur = re.findall(r"\b(USD|EUR|GBP|INR|SGD|AUD|CAD|JPY)\b", message, re.I)
                if pname == "base":
                    args[pname] = cur[0].upper()
                elif len(cur) > 1:
                    args[pname] = cur[1].upper()
            elif p.get("required") and p.get("type") in ("string",) and pname not in args and pname in ("spec", "changes", "confirm", "message", "url", "events", "plan", "interval", "method"):
                args[pname] = {
                    "spec": "{}", "changes": "{}", "confirm": "yes",
                    "message": message.strip()[:200], "url": "https://hooks.example.com/datazoic",
                    "events": "invoice.paid,payment.captured", "plan": "pro", "interval": "month",
                    "method": "card",
                }[pname]
        return args

    def _format_knowledge_answer(self, data) -> str:
        if not data or not data.get("sources"):
            return "I searched the knowledge base but couldn't find a direct match. Try rephrasing with more specific terms (e.g. product, policy name, endpoint path)."
        lines = []
        for s in data["sources"][:3]:
            snippet = " ".join(s.get("snippet", "").split())
            if len(snippet) > 260:
                snippet = snippet[:260].rsplit(" ", 1)[0] + "…"
            lines.append(f"- **{s.get('title')}** ({s.get('section')}): {snippet}")
        header = f"Here's what the Datazoic knowledge base says about that:\n"
        footer = f"\n_Sources: {len(data['sources'])} knowledge-base entries retrieved (hybrid vector + BM25)._"
        return header + "\n".join(lines) + footer

    def _format_data_answer(self, tool_name: str, data, simulated: bool) -> str:
        if data is None:
            return "Done."
        if isinstance(data, str):
            return data
        lines = []
        if isinstance(data, dict):
            msg = data.get("message")
            if msg:
                lines.append(msg)
            rows_key = next((k for k, v in data.items() if isinstance(v, list) and v and isinstance(v[0], dict)), None)
            scalar_items = [(k, v) for k, v in data.items()
                            if k not in ("message",) and not isinstance(v, (dict, list)) or
                            (isinstance(v, list) and not v and k not in ("message",))]
            if rows_key:
                rows = data[rows_key]
                label = {
                    "invoices": "invoice", "payments": "payment", "disputes": "dispute",
                    "customers": "customer", "webhooks": "webhook", "tickets": "ticket",
                    "top_customers": "top customer", "channels": "channel", "currencies": "currency",
                    "transfers": "transfer", "subscriptions": "subscription",
                    "flagged_transactions": "flagged transaction", "evidence": "evidence item",
                    "disputes": "dispute",
                }.get(rows_key, rows_key.rstrip("s"))
                if data.get("count") is not None:
                    lines.append(f"Found **{data['count']}** {label}{'s' if data['count'] != 1 else ''}:")
                for r in rows[:6]:
                    bits = []
                    for k in ("id", "status", "amount", "currency", "reason", "user_id", "customer_email",
                              "name", "email", "method", "issued_at", "created_at", "opened_at", "due_at",
                              "period", "total", "n", "total_sales", "total_refunds", "net", "sales",
                              "rate", "converted", "subject", "priority", "url", "events", "last4", "brand",
                              "total_sales", "transaction_count", "avg_sale", "period", "month",
                              "total_invoices", "pending_amount", "gross_sales", "fees", "net_revenue"):
                        if k in r and r[k] is not None:
                            v = r[k]
                            if isinstance(v, float):
                                v = f"${v:,.2f}" if MONEY_KEYS.search(k) else f"{v:,.2f}"
                            bits.append(f"{k}: {v}")
                    lines.append("- " + ", ".join(bits[:7]))
                if len(rows) > 6:
                    lines.append(f"- … and {len(rows) - 6} more")
            else:
                for k, v in scalar_items:
                    if k in ("csv",):
                        lines.append("```csv")
                        lines.append(str(v))
                        lines.append("```")
                        continue
                    display = v
                    if isinstance(v, (int, float)) and MONEY_KEYS.search(k):
                        num = f"{v:,.2f}" if isinstance(v, float) else f"{v:,}"
                        display = f"${num}" if not k.startswith("rate") else num
                    if isinstance(display, (dict, list)):
                        display = json.dumps(display)[:120]
                    lines.append(f"- **{_title(str(k))}**: {display}")
            if simulated:
                lines.append("_Note: this tool is simulated in the prototype (no live backend).")
            if not lines:
                lines.append("Done.")
        return "\n".join(lines)

    @staticmethod
    def _compact(v, limit: int = 300) -> str:
        s = v if isinstance(v, str) else json.dumps(v, default=str)
        s = " ".join(s.split())
        return s[:limit] + ("…" if len(s) > limit else "")


# ---------------------------------------------------------------------------
# OpenAI-compatible planner
# ---------------------------------------------------------------------------

class OpenAICompatLLM:
    name = "openai"

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.provider = f"openai-compat ({model})"

    def _post(self, payload: Dict) -> Dict:
        r = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload, timeout=LLM_TIMEOUT_S,
        )
        r.raise_for_status()
        return r.json()

    def _base_messages(self, message: str, session: Dict) -> List[Dict]:
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in session.get("messages", [])[-10:]:
            msgs.append({"role": m["role"], "content": m["content"]})
        msgs.append({"role": "user", "content": message})
        return msgs

    def plan(self, message: str, tool_specs: List[Dict], session: Dict) -> LLMResult:
        resp = self._post({
            "model": self.model,
            "messages": self._base_messages(message, session),
            "tools": tool_specs,
            "tool_choice": "auto",
            "temperature": 0.1,
        })
        return self._parse(resp)

    def observe(self, message: str, tool_specs: List[Dict], session: Dict,
                observations: List[Dict]) -> LLMResult:
        msgs = self._base_messages(message, session)
        # re-inject the plan step: assistant tool calls + tool results
        calls = session.get("_pending_calls", [])
        if calls:
            msgs.append({"role": "assistant", "content": None,
                         "tool_calls": [{"id": f"call_{i}", "type": "function",
                                         "function": {"name": c["name"], "arguments": json.dumps(c["args"])}}
                                        for i, c in enumerate(calls)]})
            for i, c in enumerate(calls):
                for obs in observations:
                    if obs.get("call_index") == i:
                        msgs.append({"role": "tool", "tool_call_id": f"call_{i}",
                                     "name": c["name"],
                                     "content": json.dumps(obs["result"].to_dict(), default=str)[:8000]})
        resp = self._post({
            "model": self.model,
            "messages": msgs,
            "tools": tool_specs,
            "tool_choice": "auto",
            "temperature": 0.1,
        })
        return self._parse(resp)

    @staticmethod
    def _parse(resp: Dict) -> LLMResult:
        try:
            msg = resp["choices"][0]["message"]
        except (KeyError, IndexError):
            return LLMResult(content="LLM returned an unexpected response.", provider="openai-compat")
        tool_calls = []
        for tc in msg.get("tool_calls") or []:
            try:
                args = json.loads(tc["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(ToolCall(tc["function"]["name"], args))
        if tool_calls:
            return LLMResult(tool_calls=tool_calls, provider="openai-compat")
        return LLMResult(content=(msg.get("content") or "Done.").strip(), provider="openai-compat")


# ---------------------------------------------------------------------------
# factory
# ---------------------------------------------------------------------------

def build_llm() -> HeuristicLLM | OpenAICompatLLM:
    provider = LLM_PROVIDER
    if provider == "auto":
        provider = "openai" if LLM_API_KEY else "heuristic"
    if provider == "openai":
        if not LLM_API_KEY:
            print("[config] LLM_PROVIDER=openai but no API key found — falling back to heuristic planner.")
            return HeuristicLLM()
        return OpenAICompatLLM(LLM_API_KEY, LLM_BASE_URL, LLM_MODEL)
    return HeuristicLLM()
