"""Generate the sample RAG knowledge base as markdown documents.

Writes five section files into data/docs/ — each section contains
100+ atomic entries (## headings), satisfying the brief:
"a sample database that contains minimum 100 data entries in each section".

    product_docs.md   -> 126 entries  (product documentation)
    guides.md         -> 126 entries  (step-by-step guides)
    api_reference.md  -> 115 entries  (API reference)
    policies.md       -> 115 entries  (policies & compliance)
    faq.md            -> 126 entries  (FAQ)
    -------------------------------------------------
    total             ->  608 entries

Run:  python scripts/generate_knowledge_base.py
Then: python scripts/build_rag_db.py        (chunks + embeds into the vector store)
"""
from __future__ import annotations

import random
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "data" / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

RNG = random.Random(7)
TODAY = date.today()

PRODUCT_AREAS = {
    "Invoicing": ["Invoice creation", "Line items & tax", "PDF generation", "Payment reminders",
                  "Multi-currency invoices", "Invoice summaries"],
    "Payments": ["Standard payments", "Card payments", "Bank transfer payments", "Wallet payments",
                 "Refunds", "Payment captures"],
    "Disputes & Chargebacks": ["Dispute initiation", "Evidence packages", "Auto-response rules",
                               "Dispute timelines", "Chargeback fees", "Dispute dashboards"],
    "Reporting": ["Sales reports", "Revenue reports", "Refund reports", "Monthly summaries",
                  "CSV/Excel exports", "Custom report builder"],
    "Customer Management": ["Customer profiles", "Customer balances", "Address book",
                            "Communication history", "Customer tags", "Data export"],
    "Webhooks & Events": ["Webhook subscriptions", "Event types", "Delivery retries",
                          "Signature verification", "Webhook logs", "Test events"],
    "FX Engine": ["Live exchange rates", "Currency conversion", "Rate locking",
                  "FX pairs", "Rate history", "Conversion limits"],
    "Subscriptions & Billing": ["Recurring billing", "Plan management", "Proration",
                                "Dunning & retries", "Usage-based billing", "Cancellation handling"],
    "Card Processing": ["Card tokenization", "Network tokens", "3-D Secure", "AVS & CVV checks",
                        "Card brand support", "Card vault"],
    "Bank Transfers": ["Domestic transfers", "International transfers", "Transfer tracking",
                       "SEPA support", "ACH support", "Transfer limits"],
    "Payouts": ["Merchant payouts", "Payout batches", "Payout schedules", "Payout routing rules",
                "Payout holds", "Payout reporting"],
    "Tax Engine": ["Tax calculation", "Tax ID validation", "Tax filing exports", "Tax regimes",
                   "VAT/GST support", "Tax invoices"],
    "Fraud & Risk": ["Real-time risk scoring", "Velocity rules", "Device fingerprints",
                     "Blocklists", "Case management", "Risk dashboards"],
    "Vault": ["Secret storage", "Key rotation", "Access policies", "Audit logs",
              "Environment scoping", "Secret versioning"],
    "Ledger & Accounting": ["Double-entry posting", "Chart of accounts", "Period close",
                            "Journal entries", "Ledger export", "Balance reports"],
    "Notifications": ["Email notifications", "SMS notifications", "Push notifications",
                      "Templates", "Delivery logs", "Quiet hours"],
    "Identity & KYC": ["Identity verification", "Document checks", "Biometric enrollment",
                       "KYC screening", "Rescreening", "KYC status webhooks"],
    "Marketplace": ["Seller onboarding", "Marketplace settlements", "Fee schedules",
                    "Listings", "Buyer protection", "Seller payouts"],
    "Reconciliation": ["Bank reconciliation", "Statement import", "Matching rules",
                       "Mismatch reports", "Auto-reconciliation", "Reconciliation audit"],
    "Compliance Center": ["Sanctions screening", "AML monitoring", "Regulatory filings",
                          "Audit trail", "Consent records", "Compliance reports"],
    "Support": ["Ticketing", "Priority routing", "Knowledge base", "Live chat handoff",
                "SLA tracking", "Customer feedback"],
}

VERIFY = ["checksum validation", "schema validation", "signature verification", "format validation",
          "idempotency-key deduplication", "sandbox dry-run"]


def _pick(n: int):
    return RNG.choice(n)


def _n(lo: int, hi: int) -> int:
    return RNG.randint(lo, hi)


def _upd() -> str:
    return date(TODAY.year - RNG.choice([0, 1]), RNG.randint(1, 12), RNG.randint(1, 28)).isoformat()


# ---------------------------------------------------------------------------
# 1) product documentation (120)
# ---------------------------------------------------------------------------

def gen_product_docs() -> str:
    out = ["# Product Documentation — Datazoic Pay Platform",
           "One entry per documented product capability (auto-generated sample corpus; 120 entries).", ""]
    i = 0
    for area, features in PRODUCT_AREAS.items():
        for feat in features:
            i += 1
            cap = _n(100, 5000)
            rate = _n(50, 250)
            sla = str(_n(99, 99)) + RNG.choice([".9", ".95", ".99", ".999"])
            body = (
                f"**{feat}** is a core capability of the {area} product area. "
                f"It lets businesses create, query and manage {feat.lower()} records through the API or the dashboard. "
                f"Each {feat.lower()} object carries a stable ID, timestamps, and a status lifecycle with well-defined transitions. "
                f"Key properties: idempotent writes (pass an `Idempotency-Key` header), {rate} requests/second per account, "
                f"and {sla}% availability SLA. "
                f"Typical limits: {cap:,} active records per account, payloads up to 500 KB. "
                f"Integrates with Webhooks & Events (events: `{area.lower().split()[0]}.created`, `{area.lower().split()[0]}.updated`, `{area.lower().split()[0]}.completed`) "
                f"and with Reporting for aggregated views. "
                f"Verification applied on write: {_pick(VERIFY)}."
            )
            out.append(f"## PD-{i:03d} · {area} — {feat}")
            out.append(body)
            out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 2) guides (120)
# ---------------------------------------------------------------------------

GUIDE_VERBS = ["set up", "configure", "debug", "monitor", "secure", "optimize"]
GUIDE_NOUNS = {
    "Invoicing": ["an invoice workflow", "automatic payment reminders", "multi-currency invoicing", "invoice PDF branding", "invoice summary alerts", "your first invoice via API"],
    "Payments": ["a payment flow", "card payment retries", "bank transfer tracking", "refunds end-to-end", "payment capture timing", "payment webhooks"],
    "Disputes & Chargebacks": ["a dispute response", "evidence collection", "auto-response rules", "dispute deadline tracking", "chargeback cost control", "the dispute dashboard"],
    "Reporting": ["a recurring sales report", "revenue vs GMV views", "refund analysis", "monthly close reports", "scheduled CSV exports", "a custom report"],
    "Customer Management": ["customer profiles", "balance alerts", "communication history", "customer tagging", "GDPR-safe data export", "your customer directory"],
    "Webhooks & Events": ["a webhook subscription", "event filtering", "delivery retries", "signature verification", "webhook log triage", "test events"],
    "FX Engine": ["currency conversion", "rate locking for quotes", "your FX pair watchlist", "rate history reviews", "conversion limits", "FX error handling"],
    "Subscriptions & Billing": ["recurring billing", "plan migrations", "proration rules", "dunning sequences", "usage-based billing", "graceful cancellations"],
    "Card Processing": ["card tokenization", "3-D Secure flows", "AVS/CVV check handling", "multi-brand support", "your card vault", "card decline codes"],
    "Bank Transfers": ["domestic transfers", "international transfers", "transfer tracking", "SEPA batch files", "ACH entries", "transfer limit increases"],
    "Payouts": ["merchant payouts", "payout batching", "payout schedules", "routing rules", "payout hold review", "payout reconciliation"],
    "Tax Engine": ["tax calculation", "tax ID validation", "filing exports", "multi-region tax regimes", "VAT/GST registration", "tax invoice issuance"],
    "Fraud & Risk": ["risk scoring", "velocity rules", "device fingerprinting", "blocklist management", "fraud case review", "your risk dashboard"],
    "Vault": ["secret storage", "key rotation", "least-privilege policies", "vault audit reviews", "environment scoping", "secret versioning"],
    "Ledger & Accounting": ["double-entry posting", "your chart of accounts", "period close", "journal corrections", "ledger exports", "balance review"],
    "Notifications": ["email templates", "SMS delivery", "push notifications", "template variables", "delivery log analysis", "quiet hours"],
    "Identity & KYC": ["identity verification", "document checks", "biometric enrollment", "KYC screening policies", "rescreening schedules", "KYC status webhooks"],
    "Marketplace": ["seller onboarding", "settlement cycles", "fee schedules", "listing moderation", "buyer protection claims", "seller payouts"],
    "Reconciliation": ["bank reconciliation", "statement imports", "matching rules", "mismatch triage", "auto-reconciliation", "reconciliation audits"],
    "Compliance Center": ["sanctions screening", "AML monitoring", "regulatory filing calendars", "audit trail exports", "consent record management", "compliance reports"],
    "Support": ["ticket routing", "priority rules", "knowledge base articles", "live chat handoffs", "SLA tracking", "customer feedback loops"],
}


def gen_guides() -> str:
    out = ["# Step-by-Step Guides — Datazoic Pay",
           "One entry per operational how-to (auto-generated sample corpus; 120 entries).", ""]
    i = 0
    for area, nouns in GUIDE_NOUNS.items():
        for j, noun in enumerate(nouns):
            i += 1
            verb = GUIDE_VERBS[j % len(GUIDE_VERBS)]
            pr = _pick(["a Datazoic account with the Payments scope", "an API key with write access",
                        "a team member with the Finance role", "the sandbox environment",
                        "admin access to the dashboard"])
            pit = _pick([
                "using stale API keys after rotation",
                "forgetting to set the Idempotency-Key header on retries",
                "parsing webhook payloads without signature verification",
                "ignoring rate-limit headers in high-volume flows",
                "mixing sandbox and production keys in the same client",
            ])
            body = (
                f"**Goal:** {verb} {noun} in the {area} module.\n\n"
                f"**Prerequisite:** {pr}.\n\n"
                f"**Steps**\n"
                f"1. Open the {area} section of the dashboard (or use the `/v2/{area.lower().replace(' & ', '-').split()[0]}` API group).\n"
                f"2. Create the initial record with all required fields populated; the API returns the new ID immediately.\n"
                f"3. Configure the relevant options — limits, schedules, and notification targets — on the record's settings tab.\n"
                f"4. Verify the outcome: confirm the status transition, check the Webhooks & Events log, and (where applicable) run a sandbox test first.\n\n"
                f"**Common pitfall:** {pit}. The API returns a structured error code in these cases — surface it in your alerts.\n"
                f"**Related:** PD entries for {area}; API reference section `{area.lower().replace(' ', '-')}`."
            )
            out.append(f"## G-{i:03d} · How to {verb} {noun}")
            out.append(body)
            out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 3) API reference (150)
# ---------------------------------------------------------------------------

API_NOUNS = {
    "Invoicing": ["invoices", "invoices/items", "invoices/pdf", "invoices/reminders", "invoices/summary"],
    "Payments": ["payments", "payments/cards", "payments/bank", "payments/refunds", "payments/captures"],
    "Disputes": ["disputes", "disputes/{id}/evidence", "disputes/{id}/responses", "disputes/rules", "disputes/summary"],
    "Reports": ["reports/sales", "reports/revenue", "reports/refunds", "reports/monthly", "reports/export"],
    "Customers": ["customers", "customers/{id}/balance", "customers/{id}/activity", "customers/tags", "customers/export"],
    "Webhooks": ["webhooks", "webhooks/{id}/test", "webhooks/{id}/logs", "webhooks/events", "webhooks/samples"],
    "FX": ["fx/rates", "fx/convert", "fx/lock", "fx/pairs", "fx/history"],
    "Subscriptions": ["subscriptions", "subscriptions/plans", "subscriptions/{id}/cancel", "subscriptions/dunning", "subscriptions/usage"],
    "Cards": ["cards/tokens", "cards/{token}", "cards/network-tokens", "cards/3ds/sessions", "cards/declines"],
    "Transfers": ["transfers", "transfers/{id}/tracking", "transfers/sepa/batches", "transfers/ach", "transfers/limits"],
    "Payouts": ["payouts", "payouts/batches", "payouts/schedules", "payouts/rules", "payouts/holds"],
    "Tax": ["tax/calculate", "tax/ids/validate", "tax/filings", "tax/regimes", "tax/invoices"],
    "Fraud": ["fraud/score", "fraud/rules", "fraud/devices", "fraud/blocklist", "fraud/cases"],
    "Vault": ["vault/secrets", "vault/secrets/{id}/versions", "vault/keys", "vault/policies", "vault/audit"],
    "Ledger": ["ledger/entries", "ledger/accounts", "ledger/balances", "ledger/journals", "ledger/close"],
    "Notifications": ["notifications/email", "notifications/sms", "notifications/push", "notifications/templates", "notifications/logs"],
    "Identity": ["identity/verify", "identity/documents", "identity/biometrics", "identity/kyc", "identity/rescreen"],
    "Marketplace": ["marketplace/sellers", "marketplace/settlements", "marketplace/fees", "marketplace/listings", "marketplace/claims"],
    "Reconciliation": ["reconciliation/runs", "reconciliation/statements", "reconciliation/rules", "reconciliation/mismatches", "reconciliation/audit"],
    "Compliance": ["compliance/sanctions", "compliance/aml", "compliance/filings", "compliance/audit", "compliance/reports"],
    "Support": ["support/tickets", "support/tickets/{id}", "support/feedback", "support/slas", "support/agents"],
}

ERROR_CODES = ["400 invalid_request", "401 unauthorized", "403 insufficient_scope", "404 not_found",
               "409 idempotency_conflict", "422 validation_failed", "429 rate_limited", "500 internal_error"]


def gen_api_reference() -> str:
    out = ["# API Reference — Datazoic Pay (v2 REST)",
           "One entry per documented endpoint (auto-generated sample corpus; 150 entries).", ""]
    i = 0
    for area, paths in API_NOUNS.items():
        base = f"/v2/{area.lower()}"
        for p in paths:
            i += 1
            path = f"{base}/{p}" if not p.startswith("{") else f"{base}/{p}"
            if "{" in p:
                methods = ["GET", "POST", "DELETE"]
                method = _pick(methods[:2] if "evidence" in p or "responses" in p else methods)
            elif p in ("summary", "logs", "samples", "history", "pairs", "regimes", "limits", "audit", "events"):
                method = "GET"
            elif p in ("cancel", "close", "test", "validate", "convert", "score", "verify", "calculate", "export", "tracking"):
                method = "POST"
            else:
                method = _pick(["POST", "GET", "GET", "GET"])
            noun = p.split("/")[-1].split("{")[0]
            id_param = "{" in p
            desc = {
                "GET": f"Retrieve {noun.replace('es', 'y') if noun.endswith('es') else noun} data for the {area} module.",
                "POST": f"Create or submit a {noun.replace('es', 'y') if noun.endswith('es') else noun} record in the {area} module.",
                "DELETE": f"Delete the referenced {noun} record (soft-delete; retained per the data retention policy).",
            }[method]
            params = []
            if id_param:
                params.append(f"- `id` (string, path, required): resource ID (e.g. `{noun[:3].upper()}-{_n(1000, 9999)}`)")
            params.append(f"- `limit` (integer, query, optional, default 20, max {_n(50, 200)}): page size") if method == "GET" else None
            params.append(f"- `offset` (integer, query, optional, default 0): pagination offset") if method == "GET" else None
            if method in ("POST", "DELETE"):
                params.append(f"- `amount` (number, body, conditional): monetary value in minor units where the resource is financial")
                params.append(f"- `idempotency_key` (string, header, recommended): makes retries safe")
            params.append(f"- `metadata` (object, body, optional, ≤ 50 keys): your own key-value data")
            sample_req = "{\n  \"amount\": " + str(_n(1000, 90000)) + ",\n  \"currency\": \"USD\","
            sample_req += "\n  \"metadata\": {\"source\": \"agent\"}" if method in ("POST", "DELETE") else ""
            sample_req += "\n}"
            sample_resp = ("{\n  \"id\": \"" + noun[:3].upper() + "-" + str(_n(1000, 9999)) + "\",\n  \"status\": \""
                           + _pick(["created", "active", "pending", "succeeded"]) + "\",\n  \"created_at\": \""
                           + f"{TODAY.isoformat()}T{RNG.randint(0,23):02d}:{RNG.randint(0,59):02d}:00Z\""
                           + "\n}")
            body = (
                f"**{desc}**\n\n"
                f"**Auth:** Bearer API key (`dz_live_…` / `dz_test_…`). Scopes: `{area.lower().split(' & ')[0]}:read`, `{area.lower().split(' & ')[0]}:write`.\n\n"
                f"**Parameters**\n" + "\n".join([p for p in params if p]) + "\n\n"
                f"**Example request**\n```\n{method} {path}\n{sample_req}\n```\n\n"
                f"**Example response (200/201)**\n```\n{sample_resp}\n```\n\n"
                f"**Errors:** " + ", ".join(_pick([ERROR_CODES, ERROR_CODES[:4], ERROR_CODES[1:5]])) + ". "
                f"Rate limit: {_n(60, 300)} req/min per key. Verification on write: {_pick(VERIFY)}."
            )
            out.append(f"## API-{i:03d} · {method} {path}")
            out.append(body)
            out.append("")
    # extra core endpoints to reach 150
    core = [
        ("GET /v2/health", "Liveness probe. No auth required. Returns service status, version and region."),
        ("POST /v2/oauth/token", "Exchange a client credential grant for an access token (20 min TTL)."),
        ("GET /v2/sandbox/state", "Snapshot of the current sandbox fixtures (transactions, customers, invoices)."),
        ("POST /v2/sandbox/reset", "Reset sandbox state to the canonical fixture set. Idempotent."),
        ("GET /v2/accounts/me", "The authenticated business account: id, scopes, rate limits, plan."),
        ("GET /v2/audit/recent", "The 100 most recent authenticated actions with actor, scope and IP."),
        ("GET /v2/feature-flags", "Feature flags enabled for the account (beta opt-ins)."),
        ("POST /v2/batches", "Generic bulk-write batch: up to 1000 sub-operations, applied atomically."),
        ("GET /v2/batches/{id}", "Batch status and per-operation results."),
        ("DELETE /v2/batches/{id}", "Cancel a queued batch before execution."),
    ]
    for j, (title, body) in enumerate(core, start=i + 1):
        out.append(f"## API-{j:03d} · {title}")
        out.append(body + f"\n\nRate limit: {_n(60, 300)} req/min. Verification: {_pick(VERIFY)}.")
        out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 4) policies & compliance (110)
# ---------------------------------------------------------------------------

POLICY_TOPICS = {
    "Data Retention Policy": ["Transaction record retention", "Log retention", "Deleted-account data", "Backup lifecycle", "Archival access"],
    "Invoice & Billing Retention": ["Invoice record retention", "Receipt retention", "Tax document retention", "Draft cleanup", "Record amendment"],
    "Refund Policy": ["Refund eligibility", "Refund timelines", "Partial refunds", "Refund fee handling", "Refund fraud review"],
    "Dispute & Chargeback Policy": ["Dispute response windows", "Evidence standards", "Auto-accept thresholds", "Chargeback fee allocation", "Appeal process"],
    "KYC & AML Policy": ["Onboarding identity checks", "Ongoing monitoring", "Risk-based due diligence", "Politically exposed persons", "Suspicious activity reporting"],
    "Sanctions Screening": ["Screening scope", "Name matching rules", "Watchlist updates", "False positive handling", "Freeze procedures"],
    "PCI-DSS & Card Data": ["Card data minimization", "Tokenization requirements", "3-D Secure expectations", "Scope reduction", "Assessment cadence"],
    "Data Privacy & GDPR": ["Lawful basis for processing", "Subject access requests", "Right to erasure", "International transfers", "Data processing agreements"],
    "Service Level Agreement (SLA)": ["Availability commitments", "Status page definitions", "Credit schedule", "Maintenance windows", "Severity classification"],
    "Rate Limiting & Fair Use": ["Rate limit tiers", "Burst allowance", "Priority queueing", "Abuse thresholds", "Limit increase requests"],
    "Pricing & Fees": ["Transaction fee schedule", "FX spread policy", "Dispute fee allocation", "Pricing change notice", "Fee waivers"],
    "Support & Escalation": ["Support response SLAs", "Priority definitions", "Escalation path", "Severity response times", "Business hours coverage"],
    "Security Incident Response": ["Incident classification", "Detection and triage", "Notification duties", "Containment procedures", "Post-incident review"],
    "Business Continuity & DR": ["Recovery objectives", "Failover procedure", "Data integrity checks", "Communication plan", "Exercise cadence"],
    "Access Control & IAM": ["Role definitions", "Least privilege", "Just-in-time access", "Service account policy", "Access reviews"],
    "Secrets Management Policy": ["Secret lifecycle", "Rotation schedule", "Access logging", "Secret sharing", "Compromise response"],
    "Logging & Audit Policy": ["Audit log scope", "Log immutability", "Actor attribution", "Retention of audit trails", "Audit export access"],
    "Communications & Marketing": ["Transaction email policy", "Marketing opt-in", "Do-not-contact handling", "Communication frequency caps", "Template standards"],
    "Tax Compliance": ["Tax collection duties", "Tax registration", "Filing obligations", "Tax ID verification", "Cross-border VAT"],
    "Payout Policy": ["Payout eligibility", "Payout holds and releases", "Payout frequency", "Failing payout handling", "Payout audit"],
    "Fraud Handling": ["Fraud triage", "Account restrictions", "Fund freeze policy", "Law enforcement cooperation", "Customer notification on fraud"],
    "Sandbox Usage Policy": ["Sandbox data scope", "Sandbox limits", "Production-data isolation", "Sandbox key rotation", "Fixture reset policy"],
    "Third-Party Integrations": ["Approved connector list", "Connector security review", "Data sharing boundaries", "Vendor incident policy", "Integration monitoring"],
}


def gen_policies() -> str:
    out = ["# Policies & Compliance — Datazoic Pay",
           "One entry per policy provision (auto-generated sample corpus; 110 entries).", ""]
    i = 0
    for topic, subs in POLICY_TOPICS.items():
        for sub in subs:
            i += 1
            days = _n(30, 2500)
            pct = _n(90, 99)
            body = (
                f"**Applies to:** {topic} — provision: {sub}.\n\n"
                f"All records and actions within this scope are subject to the following provision: "
                f"{sub.lower()} must be handled per the controls below. Numerical thresholds in force: "
                f"retention {_n(90, 2555)} days where storage applies, review cadence every {_n(7, 90)} days, "
                f"and {pct}% of automated checks must pass before a record is released. "
                f"Exceptions require written approval from the Compliance function and are logged in the audit trail. "
                f"Violations are reviewed by the Compliance Committee within {_n(3, 14)} business days. "
                f"Last reviewed: {_upd()} (policy version {_n(2, 9)}.{_n(0, 9)})."
            )
            out.append(f"## POL-{i:03d} · {topic}: {sub}")
            out.append(body)
            out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 5) FAQ (120)
# ---------------------------------------------------------------------------

FAQ_Q = {
    "Invoicing": ["How do I create an invoice via API?", "How long are drafts kept?", "Can invoices be multi-currency?",
                  "How are PDFs generated?", "When are reminders sent?", "How do invoice summaries work?"],
    "Payments": ["What payment methods are supported?", "How fast are refunds processed?", "What happens when a payment fails?",
                 "How do I capture a payment?", "Can I refund part of a payment?", "How are fees calculated on payments?"],
    "Disputes & Chargebacks": ["What is a dispute?", "How long do I have to respond?", "What evidence helps?",
                               "Do I pay chargeback fees if I win?", "Can disputes auto-close?", "How do I track a dispute?"],
    "Reporting": ["What is the difference between GMV and revenue?", "Which periods can I report on?",
                  "How do I export reports?", "Are reports real-time?", "Can I schedule reports?", "Where do fee numbers come from?"],
    "Customer Management": ["Where is customer data stored?", "How do I export customer data?", "Can I tag customers?",
                            "How are balances calculated?", "What happens when a customer is deleted?", "How do I link a user to invoices?"],
    "Webhooks & Events": ["How do webhooks work?", "What events exist?", "How do I verify signatures?",
                          "What happens if my endpoint is down?", "How do I test a webhook?", "Are deliveries guaranteed?"],
    "FX Engine": ["How often do rates update?", "Can I lock a rate?", "Which pairs are supported?",
                  "What is the FX spread?", "How long is rate history kept?", "Are there conversion limits?"],
    "Subscriptions & Billing": ["How does proration work?", "What is dunning?", "How do I migrate a customer to a new plan?",
                                "What happens at cancellation?", "How is usage-based billing metered?", "Can trials convert automatically?"],
    "Card Processing": ["What is tokenization?", "When is 3-D Secure required?", "What does an AVS mismatch mean?",
                        "Which card brands are supported?", "How are declines reported?", "How is card data protected?"],
    "Bank Transfers": ["How long do transfers take?", "What is the transfer limit?", "How do I track a transfer?",
                       "Which currencies are supported?", "What happens on a failed transfer?", "How are refunds on transfers handled?"],
    "Payouts": ["When are payouts processed?", "Why is my payout held?", "How are payout batches formed?",
                "Can I change payout routing?", "What triggers a payout hold?", "How do I reconcile payouts?"],
    "Tax Engine": ["How is tax calculated?", "Which taxes are supported?", "How do I validate a tax ID?",
                   "How do I export filing data?", "How do cross-border rules apply?", "What is a tax invoice?"],
    "Fraud & Risk": ["How are risk scores computed?", "What is a velocity rule?", "What does a 'review' decision mean?",
                     "How do blocklists work?", "Can I appeal a fraud flag?", "How are devices fingerprinted?"],
    "Vault": ["Where are secrets stored?", "How often must keys rotate?", "Who can read a secret?",
              "How do I audit secret access?", "Can secrets be versioned?", "What happens on rotation?"],
    "Ledger & Accounting": ["How does double-entry posting work?", "What is period close?", "How do I correct a journal entry?",
                            "How are balances computed?", "Which formats can I export?", "What is the chart of accounts?"],
    "Notifications": ["Which channels are supported?", "How do templates work?", "What are quiet hours?",
                      "How do I check delivery logs?", "Can I suppress notifications?", "How fast are SMS delivered?"],
    "Identity & KYC": ["What documents are accepted?", "How long does verification take?", "What is rescreening?",
                       "How are biometrics stored?", "What does 'under_review' mean?", "How do I get KYC status via API?"],
    "Marketplace": ["How does seller onboarding work?", "When are settlements run?", "How are marketplace fees set?",
                    "What is buyer protection?", "How are claims resolved?", "How are seller payouts triggered?"],
    "Reconciliation": ["How does auto-reconciliation match items?", "Which statement formats are supported?",
                       "What is a mismatch?", "How do I audit a reconciliation run?", "How often should I reconcile?",
                       "What happens to unmatched items?"],
    "Compliance Center": ["When is sanctions screening run?", "How are AML cases prioritized?", "What filings are automated?",
                          "How do I export the audit trail?", "How are consents recorded?", "What is in a compliance report?"],
    "Support": ["How do I create a ticket?", "What are the priority levels?", "How fast will someone respond?",
                "How does SLA tracking work?", "How do I submit feedback?", "Who can raise a ticket?"],
}


def gen_faq() -> str:
    out = ["# Frequently Asked Questions — Datazoic Pay",
           "One entry per Q&A (auto-generated sample corpus; 120 entries).", ""]
    i = 0
    for area, qs in FAQ_Q.items():
        for q in qs:
            i += 1
            ms = _n(5, 120)
            days = _n(1, 30)
            body = (
                f"**Short answer:** {_pick([
                    f'Yes — this is handled automatically in the {area} module and can also be driven via the API.',
                    f'It works through the {area} settings; the default can be overridden per record.',
                    f'This depends on your plan, but the standard behavior is documented below.',
                    f'Exactly — the {area} module keeps a full audit trail for every step.',
                ])}\n\n"
                f"In detail: the {area} module processes this with a typical latency of {ms} ms and full API support. "
                f"Timelines to remember: review turnaround is {_n(1, 5)} business days, records are kept per the applicable "
                f"retention policy, and any status change emits a webhook event within {days} minutes. "
                f"For edge cases, raise a support ticket (Support module) — the ticket is linked to the underlying record automatically. "
                f"See the API reference entries for the `{area.lower().replace(' ', '-')}` group for exact field names."
            )
            out.append(f"## FAQ-{i:03d} · {q}")
            out.append(body)
            out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
def main() -> None:
    sections = {
        "product_docs": gen_product_docs(),
        "guides": gen_guides(),
        "api_reference": gen_api_reference(),
        "policies": gen_policies(),
        "faq": gen_faq(),
    }
    total = 0
    print("Knowledge base documents:")
    for name, text in sections.items():
        n = text.count("\n## ")
        total += n
        (DOCS_DIR / f"{name}.md").write_text(text, encoding="utf-8")
        print(f"  {name:<14} {n:4d} entries   -> data/docs/{name}.md")
    print(f"  {'TOTAL':<14} {total:4d} entries")
    assert total >= 500, "expected 500+ entries across sections"
    for name, text in sections.items():
        assert text.count("\n## ") >= 100, f"section {name} has fewer than 100 entries"
    print("OK — every section has 100+ entries.")


if __name__ == "__main__":
    sys.exit(main())
