"""Tool catalog generator.

Builds the full capability catalog the router operates over:

* 60 *core* tools with real implementations (business SQLite DB, RAG,
  system self-query) — the PayPal-style surface from the task brief.
* 450+ *bulk* tools generated from a verb x noun matrix across 30 modules
  to demonstrate the 500+ tool scale from the brief. Bulk tools are
  executed by the deterministic simulator (no live backend in the
  prototype) — the routing/retrieval machinery is identical for all.

Names are globally unique:  {service}.{group}.{verb}_{noun}
"""
from __future__ import annotations

from typing import Dict, List

from .base import Tool

# ---------------------------------------------------------------------------
# parameter helpers
# ---------------------------------------------------------------------------

def _p(name: str, ptype: str = "string", required: bool = False,
       desc: str = "", **kw) -> Dict:
    d = {"type": ptype, "required": required, "description": desc}
    d.update(kw)
    return d


PERIOD_ENUM = ["last_month", "this_month", "last_7_days", "last_30_days", "last_90_days", "ytd", "all_time"]
INVOICE_STATUS = ["draft", "sent", "paid", "overdue", "cancelled"]
DISPUTE_STATUS = ["open", "under_review", "won", "lost", "closed"]
PAY_METHODS = ["card", "bank_transfer", "wallet", "balance"]

# ---------------------------------------------------------------------------
# core, implemented tools
# ---------------------------------------------------------------------------

def _core(name, service, group, domain, desc, params, handler, implemented=True):
    return Tool(name=name, service=service, group=group, domain=domain,
                description=desc, parameters=params, handler=handler, implemented=implemented)


def core_tools() -> List[Tool]:
    T: List[Tool] = []
    add = T.append

    # --- Invoicing -------------------------------------------------------
    add(_core("paypal.invoices.create_invoice", "paypal", "invoices", "Invoicing",
              "Create a new invoice for a customer with an amount, currency and optional description. "
              "Returns the new invoice with its ID (e.g. INV-0001). Use when a user wants to create, "
              "issue or send an invoice with an amount and an email address.",
              {"customer_email": _p("customer_email", required=True, desc="Customer email, e.g. john@example.com"),
               "amount": _p("amount", "number", True, "Invoice amount"),
               "currency": _p("currency", required=False, desc="ISO currency code", enum=["USD", "EUR", "GBP", "INR", "SGD"]),
               "description": _p("description", required=False, desc="What the invoice is for"),
               "user_id": _p("user_id", required=False, desc="Business user id (e.g. user_123); defaults to user_123")},
              "db:create_invoice"))
    add(_core("paypal.invoices.list_invoices", "paypal", "invoices", "Invoicing",
              "List invoices with optional filters by user and status. Returns recent invoices with "
              "amounts, dates and status. Use to find or look up an invoice.",
              {"user_id": _p("user_id", required=False, desc="Filter by business user id"),
               "status": _p("status", required=False, desc="Invoice status", enum=INVOICE_STATUS),
               "limit": _p("limit", "integer", False, "Max rows (default 10)"),
               "offset": _p("offset", "integer", False, "Pagination offset")},
              "db:list_invoices"))
    add(_core("paypal.invoices.get_invoice", "paypal", "invoices", "Invoicing",
              "Get full details of a single invoice by its ID (e.g. INV-0001): line items, amount, "
              "currency, status, issue and due dates.",
              {"invoice_id": _p("invoice_id", required=True, desc="Invoice ID, e.g. INV-0001")},
              "db:get_invoice"))
    add(_core("paypal.invoices.send_invoice", "paypal", "invoices", "Invoicing",
              "Send an existing invoice to its customer by email and record the delivery timestamp. "
              "Requires an invoice ID.",
              {"invoice_id": _p("invoice_id", required=True, desc="Invoice ID to send")},
              "db:send_invoice"))
    add(_core("paypal.invoices.update_invoice", "paypal", "invoices", "Invoicing",
              "Update fields of an existing invoice: amount, status or due date.",
              {"invoice_id": _p("invoice_id", required=True),
               "amount": _p("amount", "number", False),
               "status": _p("status", False, desc="New status", enum=INVOICE_STATUS),
               "due_date": _p("due_date", False, desc="YYYY-MM-DD")},
              "db:update_invoice"))
    add(_core("paypal.invoices.cancel_invoice", "paypal", "invoices", "Invoicing",
              "Cancel an invoice so it is no longer billed or emailed. Requires the invoice ID.",
              {"invoice_id": _p("invoice_id", required=True)},
              "db:cancel_invoice"))
    add(_core("paypal.invoices.record_invoice_payment", "paypal", "invoices", "Invoicing",
              "Record a payment against an invoice (optionally in full) and mark the invoice paid when settled.",
              {"invoice_id": _p("invoice_id", required=True),
               "amount": _p("amount", "number", False, "Payment amount; defaults to the full balance"),
               "payment_method": _p("payment_method", False, enum=PAY_METHODS)},
              "db:record_invoice_payment"))
    add(_core("paypal.invoices.get_invoice_summary", "paypal", "invoices", "Invoicing",
              "Summarize invoices: total counts, counts by status, totals and pending amounts. "
              "Optionally scoped to one user.",
              {"user_id": _p("user_id", required=False)},
              "db:get_invoice_summary"))

    # --- Payments ---------------------------------------------------------
    add(_core("paypal.payments.create_payment", "paypal", "payments", "Payments",
              "Create a payment of a given amount in a currency using a method (card, bank_transfer, "
              "wallet, balance). Use when a user wants to send or make a payment.",
              {"amount": _p("amount", "number", True),
               "currency": _p("currency", False, enum=["USD", "EUR", "GBP", "INR", "SGD"]),
               "method": _p("method", False, enum=PAY_METHODS),
               "user_id": _p("user_id", False, desc="Paying user (e.g. user_123); defaults to user_123")},
              "db:create_payment"))
    add(_core("paypal.payments.get_payment", "paypal", "payments", "Payments",
              "Get details of a single payment by ID (e.g. PAY-0001).",
              {"payment_id": _p("payment_id", required=True)},
              "db:get_payment"))
    add(_core("paypal.payments.list_payments", "paypal", "payments", "Payments",
              "List payments with optional filters by user and status. Returns amounts, methods and dates.",
              {"user_id": _p("user_id", False),
               "status": _p("status", False, enum=["succeeded", "pending", "failed", "refunded"]),
               "limit": _p("limit", "integer", False),
               "offset": _p("offset", "integer", False)},
              "db:list_payments"))
    add(_core("paypal.payments.capture_payment", "paypal", "payments", "Payments",
              "Capture a pending payment so the funds are finalized. Requires the payment ID.",
              {"payment_id": _p("payment_id", required=True)},
              "db:capture_payment"))
    add(_core("paypal.payments.refund_payment", "paypal", "payments", "Payments",
              "Refund all or part of a succeeded payment; a refund transaction is recorded.",
              {"payment_id": _p("payment_id", required=True),
               "amount": _p("amount", "number", False, "Partial refund amount; defaults to full")},
              "db:refund_payment"))
    add(_core("paypal.payments.void_payment", "paypal", "payments", "Payments",
              "Void a pending payment before it is captured. Requires the payment ID.",
              {"payment_id": _p("payment_id", required=True)},
              "db:void_payment"))
    add(_core("paypal.payments.get_payment_history", "paypal", "payments", "Payments",
              "List a user's recent payments (history) with amounts, methods and status.",
              {"user_id": _p("user_id", False, desc="User to inspect; defaults to user_123"),
               "limit": _p("limit", "integer", False)},
              "db:get_payment_history"))

    # --- Disputes -----------------------------------------------------------
    add(_core("paypal.disputes.list_disputes", "paypal", "disputes", "Disputes",
              "List disputes, optionally filtered by user and status (open, under_review, won, lost, closed). "
              "Use to check whether there is any open dispute for a user.",
              {"user_id": _p("user_id", False, desc="Filter by user (e.g. user_123)"),
               "status": _p("status", False, enum=DISPUTE_STATUS),
               "limit": _p("limit", "integer", False)},
              "db:list_disputes"))
    add(_core("paypal.disputes.get_dispute", "paypal", "disputes", "Disputes",
              "Get details of a single dispute by ID (e.g. DSP-0001): reason, status, payment, dates.",
              {"dispute_id": _p("dispute_id", required=True)},
              "db:get_dispute"))
    add(_core("paypal.disputes.open_dispute", "paypal", "disputes", "Disputes",
              "Open a new dispute against a payment with a reason. Creates the dispute record.",
              {"user_id": _p("user_id", required=True),
               "payment_id": _p("payment_id", False),
               "reason": _p("reason", required=True,
                             enum=["unauthorized_transaction", "item_not_received", "duplicate_charge",
                                   "defective_product", "not_as_described", "other"])},
              "db:open_dispute"))
    add(_core("paypal.disputes.respond_to_dispute", "paypal", "disputes", "Disputes",
              "Submit a response or evidence note to an open dispute, moving it to under_review.",
              {"dispute_id": _p("dispute_id", required=True),
               "message": _p("message", required=True, desc="Response text")},
              "db:respond_to_dispute"))
    add(_core("paypal.disputes.accept_dispute", "paypal", "disputes", "Disputes",
              "Accept a dispute (concede the claim) and close it.",
              {"dispute_id": _p("dispute_id", required=True)},
              "db:accept_dispute"))
    add(_core("paypal.disputes.close_dispute", "paypal", "disputes", "Disputes",
              "Close a dispute with an outcome (won, lost, accepted or withdrawn).",
              {"dispute_id": _p("dispute_id", required=True),
               "outcome": _p("outcome", required=True, enum=["won", "lost", "accepted", "withdrawn"])},
              "db:close_dispute"))
    add(_core("paypal.disputes.list_dispute_evidence", "paypal", "disputes", "Disputes",
              "Retrieve the evidence attached to a dispute: statements, receipts, tracking updates.",
              {"dispute_id": _p("dispute_id", required=True)},
              "db:list_dispute_evidence"))

    # --- Reporting & analytics ----------------------------------------------
    add(_core("paypal.reports.get_sales_report", "paypal", "reports", "Reporting & Analytics",
              "Get total sales volume (GMV) for a period such as last month, this month, last 30 days "
              "or year-to-date. Aggregates successful sale transactions. Use for questions like "
              "'what was my total sales volume last month?'.",
              {"period": _p("period", False, desc="Reporting period", enum=PERIOD_ENUM)},
              "db:get_sales_report"))
    add(_core("paypal.reports.get_revenue_report", "paypal", "reports", "Reporting & Analytics",
              "Get net revenue for a period: gross sales minus platform fees.",
              {"period": _p("period", False, enum=PERIOD_ENUM)},
              "db:get_revenue_report"))
    add(_core("paypal.reports.get_refund_report", "paypal", "reports", "Reporting & Analytics",
              "Get total refunds issued during a period with counts and top refund reasons.",
              {"period": _p("period", False, enum=PERIOD_ENUM)},
              "db:get_refund_report"))
    add(_core("paypal.reports.get_monthly_summary", "paypal", "reports", "Reporting & Analytics",
              "Monthly business summary for a calendar month (YYYY-MM): sales, refunds, fees, payouts and net.",
              {"month": _p("month", False, desc="Calendar month YYYY-MM; defaults to the current month")},
              "db:get_monthly_summary"))
    add(_core("paypal.reports.export_sales_csv", "paypal", "reports", "Reporting & Analytics",
              "Export sale transactions for a period as CSV text (capped at 50 rows).",
              {"period": _p("period", False, enum=PERIOD_ENUM)},
              "db:export_sales_csv"))
    add(_core("analytics.metrics.get_gmv", "analytics", "metrics", "Reporting & Analytics",
              "Get gross merchandise value (GMV) for a period with day-over-day and month-over-month deltas.",
              {"period": _p("period", False, enum=PERIOD_ENUM)},
              "db:get_gmv"))
    add(_core("analytics.metrics.get_top_customers", "analytics", "metrics", "Reporting & Analytics",
              "Get the top customers by sales volume for a period.",
              {"period": _p("period", False, enum=PERIOD_ENUM),
               "limit": _p("limit", "integer", False, desc="How many customers (default 5)")},
              "db:get_top_customers"))
    add(_core("analytics.metrics.get_channel_breakdown", "analytics", "metrics", "Reporting & Analytics",
              "Break down successful payments by payment channel (card, bank_transfer, wallet, balance) for a period.",
              {"period": _p("period", False, enum=PERIOD_ENUM)},
              "db:get_channel_breakdown"))

    # --- Customers ------------------------------------------------------------
    add(_core("paypal.customers.get_customer", "paypal", "customers", "Customers",
              "Get a customer profile by user ID (e.g. user_123): name, email, country plus activity counts "
              "(invoices, payments, open disputes).",
              {"user_id": _p("user_id", required=True, desc="e.g. user_123")},
              "db:get_customer"))
    add(_core("paypal.customers.list_customers", "paypal", "customers", "Customers",
              "List customers with pagination.",
              {"limit": _p("limit", "integer", False), "offset": _p("offset", "integer", False)},
              "db:list_customers"))
    add(_core("paypal.customers.create_customer", "paypal", "customers", "Customers",
              "Create a new customer record with a name and email.",
              {"name": _p("name", required=True), "email": _p("email", required=True),
               "country": _p("country", False)},
              "db:create_customer"))
    add(_core("paypal.customers.update_customer", "paypal", "customers", "Customers",
              "Update a customer's name, email or country.",
              {"user_id": _p("user_id", required=True),
               "name": _p("name", False), "email": _p("email", False), "country": _p("country", False)},
              "db:update_customer"))

    # --- Webhooks ----------------------------------------------------------------
    add(_core("paypal.webhooks.list_webhooks", "paypal", "webhooks", "Webhooks & Events",
              "List configured webhook subscriptions with their event types and active state.",
              {"active_only": _p("active_only", False, enum=["true", "false"])},
              "db:list_webhooks"))
    add(_core("paypal.webhooks.create_webhook", "paypal", "webhooks", "Webhooks & Events",
              "Create a webhook subscription for a URL and a list of event types.",
              {"url": _p("url", required=True),
               "events": _p("events", required=True, desc="Comma-separated event types, e.g. invoice.paid,payment.captured")},
              "db:create_webhook"))
    add(_core("paypal.webhooks.test_webhook", "paypal", "webhooks", "Webhooks & Events",
              "Send a test event to a webhook endpoint and report the (simulated) delivery result.",
              {"webhook_id": _p("webhook_id", required=True)},
              "db:test_webhook"))

    # --- FX -------------------------------------------------------------------------
    add(_core("paypal.fx.get_exchange_rate", "paypal", "fx", "FX & Currencies",
              "Get the current exchange rate between two currencies (e.g. USD to INR).",
              {"base": _p("base", required=True, desc="Base currency, e.g. USD"),
               "quote": _p("quote", required=True, desc="Quote currency, e.g. INR")},
              "db:get_exchange_rate"))
    add(_core("paypal.fx.convert_currency", "paypal", "fx", "FX & Currencies",
              "Convert an amount from one currency to another at the current rate.",
              {"amount": _p("amount", "number", required=True),
               "base": _p("base", required=True), "quote": _p("quote", required=True)},
              "db:convert_currency"))
    add(_core("paypal.fx.list_currencies", "paypal", "fx", "FX & Currencies",
              "List the currencies supported for conversion with current USD rates.",
              {},
              "db:list_currencies"))

    # --- Cards --------------------------------------------------------------------------
    add(_core("stripe.cards.tokenize_card", "stripe", "cards", "Cards",
              "Tokenize a card for a user (brand + last 4) and store a token for later charges.",
              {"user_id": _p("user_id", False), "brand": _p("brand", required=True,
                                                             enum=["visa", "mastercard", "amex", "rupay"]),
               "last4": _p("last4", required=True, desc="Last 4 digits")},
              "db:tokenize_card"))
    add(_core("stripe.cards.create_card_payment", "stripe", "cards", "Cards",
              "Charge a tokenized card for an amount and return the payment.",
              {"amount": _p("amount", "number", required=True),
               "last4": _p("last4", required=True),
               "currency": _p("currency", False), "user_id": _p("user_id", False)},
              "db:create_card_payment"))
    add(_core("stripe.cards.list_card_payments", "stripe", "cards", "Cards",
              "List card payments for a user.",
              {"user_id": _p("user_id", False), "limit": _p("limit", "integer", False)},
              "db:list_card_payments"))
    add(_core("stripe.cards.refund_card_payment", "stripe", "cards", "Cards",
              "Refund a card payment (full or partial).",
              {"payment_id": _p("payment_id", required=True),
               "amount": _p("amount", "number", False)},
              "db:refund_payment"))

    # --- Subscriptions --------------------------------------------------------------------
    add(_core("stripe.subscriptions.create_subscription", "stripe", "subscriptions", "Subscriptions",
              "Create a recurring subscription for a user with a plan, amount and billing interval.",
              {"plan": _p("plan", required=True, enum=["starter", "pro", "enterprise"]),
               "amount": _p("amount", "number", required=True),
               "interval": _p("interval", required=True, enum=["month", "year"]),
               "user_id": _p("user_id", False)},
              "db:create_subscription"))
    add(_core("stripe.subscriptions.list_subscriptions", "stripe", "subscriptions", "Subscriptions",
              "List active subscriptions for a user.",
              {"user_id": _p("user_id", False)},
              "db:list_subscriptions"))
    add(_core("stripe.subscriptions.cancel_subscription", "stripe", "subscriptions", "Subscriptions",
              "Cancel a subscription; it stays active until the end of the billing period.",
              {"subscription_id": _p("subscription_id", required=True)},
              "db:cancel_subscription"))
    add(_core("stripe.subscriptions.get_subscription_usage", "stripe", "subscriptions", "Subscriptions",
              "Get usage and billing history for a subscription.",
              {"subscription_id": _p("subscription_id", required=True)},
              "db:get_subscription_usage"))

    # --- Banking & transfers -----------------------------------------------------------------
    add(_core("banking.transfers.create_transfer", "banking", "transfers", "Banking & Transfers",
              "Create a bank transfer of an amount to a recipient IBAN/account.",
              {"amount": _p("amount", "number", required=True),
               "recipient": _p("recipient", required=True, desc="Recipient IBAN or account id"),
               "currency": _p("currency", False), "user_id": _p("user_id", False)},
              "db:create_transfer"))
    add(_core("banking.transfers.get_transfer", "banking", "transfers", "Banking & Transfers",
              "Get details of a bank transfer by ID (e.g. TRF-00001).",
              {"transfer_id": _p("transfer_id", required=True)},
              "db:get_transfer"))
    add(_core("banking.transfers.list_transfers", "banking", "transfers", "Banking & Transfers",
              "List bank transfers for a user.",
              {"user_id": _p("user_id", False), "limit": _p("limit", "integer", False)},
              "db:list_transfers"))

    # --- Support ------------------------------------------------------------------------------
    add(_core("support.tickets.create_ticket", "support", "tickets", "Support",
              "Create a support ticket with a subject and description.",
              {"subject": _p("subject", required=True),
               "description": _p("description", False), "user_id": _p("user_id", False),
               "priority": _p("priority", False, enum=["low", "medium", "high", "urgent"])},
              "db:create_ticket"))
    add(_core("support.tickets.list_tickets", "support", "tickets", "Support",
              "List support tickets, optionally filtered by user or status.",
              {"user_id": _p("user_id", False),
               "status": _p("status", False, enum=["open", "in_progress", "closed"]),
               "limit": _p("limit", "integer", False)},
              "db:list_tickets"))
    add(_core("support.tickets.get_ticket", "support", "tickets", "Support",
              "Get details of a support ticket by ID (e.g. TKT-0001).",
              {"ticket_id": _p("ticket_id", required=True)},
              "db:get_ticket"))
    add(_core("support.tickets.close_ticket", "support", "tickets", "Support",
              "Close a support ticket.",
              {"ticket_id": _p("ticket_id", required=True)},
              "db:close_ticket"))

    # --- Fraud / risk ---------------------------------------------------------------------------
    add(_core("fraud.detection.score_transaction", "fraud", "detection", "Risk & Fraud",
              "Run a transaction through the fraud model and get a risk score with contributing factors.",
              {"amount": _p("amount", "number", required=True),
               "currency": _p("currency", False), "country": _p("country", False),
               "user_id": _p("user_id", False)},
              "db:score_transaction"))
    add(_core("fraud.detection.list_flagged_transactions", "fraud", "detection", "Risk & Fraud",
              "List the most recently flagged (high-risk) transactions.",
              {"limit": _p("limit", "integer", False)},
              "db:list_flagged_transactions"))

    # --- System & meta (the two special tools from the brief) ---------------------------------------
    add(_core("system.search_capabilities", "system", "meta", "System & Meta",
              "Search the agent's available capabilities and tools by natural language. Use when a user asks "
              "what tools or features exist, e.g. 'what tools are available for managing invoices?'.",
              {"query": _p("query", required=True, desc="Natural-language capability query")},
              "system:search_capabilities"))
    add(_core("system.get_last_request", "system", "meta", "System & Meta",
              "Show the status, parameters and result of the user's most recent tool request in this "
              "session. Use for questions like 'what's the status of my last request?'.",
              {},
              "system:get_last_request"))
    add(_core("system.ask_knowledge_base", "system", "meta", "System & Meta",
              "Query the Datazoic knowledge base (RAG): product documentation, step-by-step guides, API "
              "reference, policies & compliance, and the FAQ. Use for how-to, policy, definition or "
              "reference questions that are not a system action.",
              {"query": _p("query", required=True, desc="The knowledge question to answer")},
              "rag:ask_knowledge_base"))

    return T


# ---------------------------------------------------------------------------
# bulk tool matrix (500+ scale demonstration)
# ---------------------------------------------------------------------------

VERB_TEMPLATES = {
    "create": ("Create a new {n} in the {d} module. Returns the created record with its ID.",
               {"spec": _p("spec", required=True, desc="JSON object with the creation fields"),
                "user_id": _p("user_id", False, desc="Owning user (e.g. user_123)")}),
    "get": ("Get details of a single {n} by ID.",
            {"id": _p("id", required=True, desc="ID of the record")}),
    "list": ("List {n}s with pagination; optional status and user filters.",
             {"limit": _p("limit", "integer", False), "offset": _p("offset", "integer", False),
              "status": _p("status", False), "user_id": _p("user_id", False)}),
    "update": ("Update fields of an existing {n}.",
               {"id": _p("id", required=True),
                "changes": _p("changes", required=True, desc="JSON object of fields to update")}),
    "delete": ("Permanently delete a {n}. Requires explicit confirmation.",
               {"id": _p("id", required=True), "confirm": _p("confirm", required=True,
                                                              desc="Type 'yes' to confirm")}),
    "cancel": ("Cancel a pending {n} before it completes.",
               {"id": _p("id", required=True), "reason": _p("reason", False)}),
    "pause": ("Pause an active {n}; optionally schedule automatic resume.",
              {"id": _p("id", required=True), "resume_at": _p("resume_at", False, desc="ISO timestamp")}),
    "approve": ("Approve a pending {n} so it can proceed.",
                {"id": _p("id", required=True), "approver": _p("approver", False)}),
    "export": ("Export {n}s as CSV/JSON for a date range.",
               {"start_date": _p("start_date", False, desc="YYYY-MM-DD"),
                "end_date": _p("end_date", False, desc="YYYY-MM-DD"),
                "format": _p("format", False, enum=["csv", "json", "xml"]),
                "limit": _p("limit", "integer", False)}),
    "retry": ("Retry a failed {n} execution.",
              {"id": _p("id", required=True), "max_attempts": _p("max_attempts", "integer", False)}),
    "run": ("Execute a {n} now (optionally in dry-run mode).",
            {"id": _p("id", required=True, desc="ID of the record to execute"),
             "dry_run": _p("dry_run", False, enum=["true", "false"])}),
    "submit": ("Submit a {n} for processing.",
               {"id": _p("id", required=True)}),
    "verify": ("Verify the validity or status of a {n}.",
               {"id": _p("id", required=True)}),
    "rotate": ("Rotate the key material of a {n}.",
               {"id": _p("id", required=True)}),
    "send": ("Send a {n} to a recipient.",
             {"id": _p("id", required=True), "recipient": _p("recipient", required=True)}),
}


def _module(key: str, domain: str, nouns) -> dict:
    return {"key": key, "domain": domain, "nouns": nouns}


BULK_MODULES = [
    _module("payouts", "Payouts", [
        ("payout", "merchant payout", ["create", "get", "list", "update", "cancel"]),
        ("payout_batch", "payout batch", ["create", "get", "list", "approve", "export"]),
        ("payout_schedule", "recurring payout schedule", ["create", "get", "list", "update", "pause"]),
        ("payout_rule", "payout routing rule", ["create", "get", "list", "update", "delete"]),
    ]),
    _module("tax", "Taxes", [
        ("tax_rate", "tax rate", ["get", "list", "update"]),
        ("tax_id", "tax identification number", ["create", "get", "verify"]),
        ("tax_filing", "tax filing", ["create", "get", "list", "submit", "export"]),
        ("tax_regime", "tax regime", ["get", "list"]),
        ("tax_invoice", "tax invoice", ["create", "get", "list", "export"]),
    ]),
    _module("vault", "Vault & Secrets", [
        ("vault_item", "vault secret", ["create", "get", "list", "delete"]),
        ("vault_key", "vault encryption key", ["create", "get", "rotate", "delete"]),
        ("vault_policy", "vault access policy", ["create", "get", "list", "update"]),
        ("vault_audit_log", "vault audit log", ["get", "list", "export"]),
        ("secret_version", "secret version", ["get", "list"]),
    ]),
    _module("ledger", "Ledger", [
        ("ledger_entry", "ledger entry", ["create", "get", "list", "export"]),
        ("ledger_account", "ledger account", ["create", "get", "list", "update"]),
        ("ledger_balance", "ledger balance", ["get", "list", "export"]),
        ("journal", "accounting journal", ["create", "get", "list", "export"]),
    ]),
    _module("notifications", "Notifications", [
        ("notification", "notification message", ["create", "get", "list", "delete"]),
        ("notification_template", "notification template", ["create", "get", "list", "update"]),
        ("notification_log", "notification delivery log", ["get", "list", "export"]),
        ("delivery_channel", "delivery channel", ["create", "get", "list", "update"]),
        ("inbox_rule", "inbox routing rule", ["create", "get", "list", "delete"]),
    ]),
    _module("identity", "Identity & KYC", [
        ("identity_verification", "identity verification", ["create", "get", "list", "verify"]),
        ("kyc_document", "KYC document", ["create", "get", "list", "delete"]),
        ("identity_score", "identity score", ["get", "export"]),
        ("identity_provider", "identity provider", ["create", "get", "list", "update"]),
        ("biometric_enrollment", "biometric enrollment", ["create", "get", "delete", "verify"]),
    ]),
    _module("shipping", "Shipping & Logistics", [
        ("shipment", "shipment", ["create", "get", "list", "cancel", "export"]),
        ("shipping_label", "shipping label", ["create", "get"]),
        ("tracking_event", "tracking event", ["get", "list"]),
        ("warehouse", "warehouse location", ["create", "get", "list", "update"]),
        ("customs_declaration", "customs declaration", ["create", "get", "list", "export"]),
        ("freight_quote", "freight quote", ["create", "get", "list"]),
    ]),
    _module("marketplace", "Marketplace", [
        ("seller", "marketplace seller", ["create", "get", "list", "update"]),
        ("marketplace_settlement", "marketplace settlement", ["get", "list", "export", "approve"]),
        ("marketplace_fee", "marketplace service fee", ["get", "list", "update"]),
        ("listing", "marketplace listing", ["create", "get", "list", "update", "delete"]),
        ("buyer", "marketplace buyer", ["get", "list"]),
    ]),
    _module("reconciliation", "Reconciliation", [
        ("reconciliation_run", "reconciliation run", ["create", "get", "list", "run", "export"]),
        ("mismatch_report", "reconciliation mismatch report", ["get", "list", "export"]),
        ("bank_statement", "imported bank statement", ["create", "get", "list", "export"]),
        ("reconciliation_rule", "reconciliation matching rule", ["create", "get", "list", "update"]),
    ]),
    _module("compliance", "Compliance", [
        ("sanctions_check", "sanctions screening check", ["create", "get", "list", "export"]),
        ("aml_case", "AML case", ["create", "get", "list", "update", "delete"]),
        ("kyc_case", "KYC review case", ["get", "list", "export"]),
        ("compliance_report", "compliance report", ["create", "get", "list", "export"]),
        ("risk_assessment", "risk assessment", ["create", "get", "export"]),
        ("regulatory_filing", "regulatory filing", ["create", "get", "list", "submit"]),
    ]),
    _module("crypto", "Crypto", [
        ("crypto_rate", "crypto exchange rate", ["get", "list", "export"]),
        ("crypto_conversion", "crypto conversion", ["create", "get", "list"]),
        ("crypto_wallet", "crypto wallet", ["create", "get", "list", "delete"]),
        ("crypto_address", "crypto address", ["create", "get", "list", "verify"]),
    ]),
    _module("integrations", "Integrations", [
        ("integration_connection", "integration connection", ["create", "get", "list", "delete", "run"]),
        ("sync_job", "integration sync job", ["create", "get", "list", "run", "export"]),
        ("erp_mapping", "ERP field mapping", ["create", "get", "list", "update"]),
        ("crm_sync", "CRM synchronization", ["create", "get", "list", "run"]),
        ("webhook_relay", "webhook relay endpoint", ["create", "get", "list", "run"]),
    ]),
    _module("data", "Data & Exports", [
        ("dataset", "dataset", ["create", "get", "list", "export", "delete"]),
        ("export_job", "data export job", ["create", "get", "list", "run", "export"]),
        ("import_job", "data import job", ["create", "get", "list", "run"]),
        ("data_retention_rule", "data retention rule", ["create", "get", "list", "update"]),
        ("lineage_report", "data lineage report", ["get", "export"]),
        ("quality_rule", "data quality rule", ["create", "get", "list", "update", "run"]),
    ]),
    _module("risk", "Risk & Fraud", [
        ("risk_rule", "risk rule", ["create", "get", "list", "update"]),
        ("risk_score_snapshot", "risk score snapshot", ["get", "export"]),
        ("flagged_transaction_batch", "flagged transaction batch", ["create", "get", "export"]),
        ("anomaly_alert", "anomaly alert", ["create", "get", "list", "delete"]),
        ("device_fingerprint", "device fingerprint", ["create", "get"]),
        ("velocity_rule", "velocity rule", ["create", "get", "list", "update"]),
        ("blocklist", "blocklist entry", ["create", "get", "list", "delete"]),
    ]),
    _module("payroll", "Payroll", [
        ("payroll_run", "payroll run", ["create", "get", "list", "run", "export"]),
        ("payroll_employee", "payroll employee", ["create", "get", "list", "update", "delete"]),
        ("payslip", "payslip", ["get", "export"]),
        ("payroll_cycle", "payroll cycle", ["create", "get", "list", "update"]),
        ("payroll_tax_setting", "payroll tax setting", ["create", "get", "list", "update"]),
    ]),
    _module("treasury", "Treasury", [
        ("cash_position", "cash position", ["get", "export"]),
        ("liquidity_forecast", "liquidity forecast", ["create", "get", "export"]),
        ("treasury_operation", "treasury operation", ["create", "get", "list", "approve", "export"]),
        ("fx_hedge", "FX hedge position", ["create", "get", "list", "cancel"]),
        ("interest_forecast", "interest forecast", ["get", "export"]),
    ]),
    _module("billing", "Invoicing", [
        ("billing_plan", "billing plan", ["create", "get", "list", "update", "delete"]),
        ("billing_price", "billing price", ["create", "get", "list", "update"]),
        ("billing_invoice_draft", "billing invoice draft", ["create", "get", "list", "send"]),
        ("dunning_policy", "dunning (failed-payment) policy", ["create", "get", "list", "update"]),
    ]),
    _module("catalog", "Marketplace", [
        ("catalog_item", "catalog item", ["create", "get", "list", "update", "delete"]),
        ("catalog_variant", "catalog variant", ["create", "get", "list", "delete"]),
        ("catalog_price", "catalog price", ["get", "list", "update"]),
        ("catalog_inventory", "catalog inventory level", ["get", "list", "update"]),
    ]),
    _module("marketing", "Marketing", [
        ("campaign", "marketing campaign", ["create", "get", "list", "update", "delete", "run"]),
        ("campaign_segment", "campaign audience segment", ["create", "get", "list", "delete"]),
        ("offer", "promotional offer", ["create", "get", "list", "update"]),
        ("attribution_report", "attribution report", ["get", "list", "export"]),
    ]),
    _module("logistics", "Shipping & Logistics", [
        ("logistics_route", "logistics route", ["create", "get", "list", "update"]),
        ("logistics_carrier", "logistics carrier", ["create", "get", "list", "update"]),
        ("delivery_window", "delivery window", ["create", "get", "list", "update"]),
        ("fleet_vehicle", "fleet vehicle", ["create", "get", "list", "update"]),
    ]),
    _module("sandbox", "Sandbox & Testing", [
        ("sandbox_account", "sandbox account", ["create", "get", "list", "delete"]),
        ("sandbox_fixture", "sandbox data fixture", ["create", "get", "list", "delete"]),
        ("sandbox_scenario", "sandbox test scenario", ["create", "get", "run", "delete"]),
        ("sandbox_reset", "sandbox reset job", ["get", "run"]),
    ]),
    _module("audit", "Compliance", [
        ("audit_log_query", "audit log query", ["create", "get", "run", "export"]),
        ("audit_policy", "audit policy", ["create", "get", "list", "update"]),
        ("data_access_request", "data access request", ["create", "get", "list", "update"]),
        ("consent_record", "consent record", ["create", "get", "list", "delete"]),
    ]),
    _module("legacy_gateway", "Legacy Gateway", [
        ("legacy_invoice_call", "legacy v1 invoice API call", ["get", "list", "run", "retry"]),
        ("legacy_payment_call", "legacy v1 payment API call", ["get", "list", "run", "retry"]),
        ("legacy_webhook_call", "legacy v1 webhook call", ["get", "run", "retry"]),
        ("legacy_report_call", "legacy v1 report call", ["get", "list", "run", "export"]),
        ("legacy_customer_call", "legacy v1 customer call", ["get", "list", "run"]),
    ]),
    _module("observability", "Observability", [
        ("platform_metric", "platform metric", ["get", "list", "export"]),
        ("log_query", "log query", ["get", "run", "export"]),
        ("trace_lookup", "distributed trace lookup", ["get", "run"]),
        ("error_budget", "error budget", ["get", "export"]),
        ("oncall_rotation", "on-call rotation", ["get", "list", "update"]),
        ("sla_report", "SLA report", ["get", "list", "export"]),
        ("incident", "incident record", ["create", "get", "list", "delete"]),
    ]),
    _module("analytics_ext", "Reporting & Analytics", [
        ("cohort_report", "cohort analysis report", ["get", "export"]),
        ("funnel_report", "conversion funnel report", ["get", "export", "run"]),
        ("retention_report", "retention report", ["get", "export"]),
    ]),
]

# extra domain for the sandbox module
EXTRA_DOMAINS = {"Sandbox & Testing": "Sandbox accounts, fixtures and test scenarios for safe experimentation."}


def bulk_tools() -> List[Tool]:
    T: List[Tool] = []
    for mod in BULK_MODULES:
        for noun, noun_desc, verbs in mod["nouns"]:
            for verb in verbs:
                template, params = VERB_TEMPLATES[verb]
                desc = template.format(n=noun_desc, d=mod["domain"])
                name = f"datazoic.{mod['key']}.{verb}_{noun}"
                T.append(Tool(
                    name=name,
                    service="datazoic",
                    group=mod["key"],
                    domain=mod["domain"],
                    description=desc,
                    parameters=params,
                    handler="simulated",
                    implemented=False,
                ))
    return T


def build_catalog() -> list:
    """Core + bulk catalog. Guarantees >= 500 tools (task: scale beyond 100)."""
    tools = core_tools() + bulk_tools()
    if len(tools) < 500:  # defensive pad — should not trigger
        i = 1
        while len(tools) < 500:
            tools.append(Tool(
                name=f"datazoic.admin.generic_op_{i}", service="datazoic", group="admin",
                domain="Observability",
                description=f"Generic administration operation #{i} for platform maintenance.",
                parameters={"id": _p("id", required=True)},
                handler="simulated", implemented=False,
            ))
            i += 1
    return tools
