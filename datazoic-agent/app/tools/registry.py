"""Tool registry: the single source of truth for every agent capability.

The registry stores all 500+ tools with rich metadata (service, group,
routing domain, parameter schema). At startup the router precomputes an
embedding + lexical index over tool names/descriptions so per-turn tool
selection is a vector lookup, never a "dump all tools into the prompt".
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Dict, List, Optional

from .base import Tool

# Routing domains: each maps to a short description the router embeds, so
# query -> domain -> candidate tools (two-level funnel keeps context small).
DOMAINS: Dict[str, str] = {
    "Invoicing": "Create, send, update, cancel and track invoices; invoice line items, totals and summaries.",
    "Payments": "Create, capture, refund and void payments; payment history and methods (card, bank, wallet, balance).",
    "Disputes": "Open, list, respond to and close payment disputes; dispute evidence and outcomes.",
    "Reporting & Analytics": "Sales volume (GMV), revenue, refunds, monthly summaries, exports, top customers, channel breakdown.",
    "Customers": "Customer profiles, balances, and account updates.",
    "Webhooks & Events": "Webhook subscriptions, event types, delivery testing.",
    "FX & Currencies": "Exchange rates and currency conversion.",
    "Cards": "Card tokenization, card payments and card refunds.",
    "Subscriptions": "Recurring billing: subscriptions, plans, usage and cancellation.",
    "Banking & Transfers": "Bank account transfers, transfers and balances.",
    "Payouts": "Merchant payouts, payout batches, schedules and rules.",
    "Taxes": "Tax calculation, tax IDs, filings and regimes.",
    "Vault & Secrets": "Secure storage of API keys and credentials, key rotation.",
    "Ledger": "Double-entry ledger entries, balances and reconciliation.",
    "Notifications": "Email, SMS and push notifications, templates.",
    "Identity & KYC": "Identity verification, KYC status and documents.",
    "Shipping & Logistics": "Shipments, tracking and logistics.",
    "Marketplace": "Marketplace sellers, settlements and fees.",
    "Reconciliation": "Bank vs platform reconciliation, mismatches.",
    "Compliance": "Sanctions screening, AML, KYC cases.",
    "Crypto": "Crypto rates and conversion.",
    "Integrations": "Third-party system sync (ERP, CRM, accounting).",
    "Data & Exports": "Datasets, imports, exports and scheduled jobs.",
    "Risk & Fraud": "Transaction risk scoring, flagged transactions, fraud rules.",
    "Payroll": "Payroll runs, employees and payslips.",
    "Treasury": "Cash position, liquidity and treasury operations.",
    "Support": "Support tickets, priorities and resolution.",
    "Legacy Gateway": "Legacy v1/v2 gateway calls, retries and status.",
    "Observability": "Platform metrics, logs, traces and audit.",
    "Marketing": "Campaigns, segments and offers.",
    "Sandbox & Testing": "Sandbox accounts, fixtures and test scenarios for safe experimentation.",
    "System & Meta": "Search available capabilities, inspect the agent's own request history, and query the knowledge base (RAG).",
}


class Registry:
    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}
        self._lock = threading.RLock()

    def register(self, tool: Tool) -> None:
        with self._lock:
            if tool.name in self._tools:
                raise ValueError(f"duplicate tool name: {tool.name}")
            self._tools[tool.name] = tool

    def register_many(self, tools: List[Tool]) -> None:
        for t in tools:
            self.register(t)

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def all(self) -> List[Tool]:
        return list(self._tools.values())

    def domains(self) -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {}
        for t in self._tools.values():
            out.setdefault(t.domain, []).append(t.name)
        return out

    def by_domain(self, domain: str) -> List[Tool]:
        return [t for t in self._tools.values() if t.domain == domain]

    def count(self) -> int:
        return len(self._tools)

    def implemented_count(self) -> int:
        return sum(1 for t in self._tools.values() if t.implemented)

    def dump_json(self, path: str | Path) -> None:
        """Write the full catalog to disk for inspection / audit."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "total_tools": self.count(),
            "implemented": self.implemented_count(),
            "simulated": self.count() - self.implemented_count(),
            "domains": {d: len(v) for d, v in sorted(self.domains().items())},
            "tools": [
                {
                    "name": t.name, "service": t.service, "group": t.group, "domain": t.domain,
                    "description": t.description, "parameters": t.parameters,
                    "handler": t.handler, "implemented": t.implemented,
                }
                for t in sorted(self._tools.values(), key=lambda x: x.name)
            ],
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
