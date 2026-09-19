"""End-to-end tests for the Datazoic agentic platform.

Covers: tool catalog scale, RAG knowledge base (100+ per section), hybrid
retrieval quality, router funneling, and the agent loop on the exact
example queries from the Datazoic task brief.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.main import _bootstrap  # noqa: E402


@pytest.fixture(scope="module")
def state():
    s = _bootstrap()
    s["ctx"]["session_holder"].session_id = "test-session"
    return s


SID = [None]  # shared across tests so "last request" / memory behave like a real chat


def _chat(state, message):
    s = state["ctx"]["session_holder"]
    s.session_id = SID[0]
    r = state["agent"].chat(message, SID[0])
    SID[0] = r["session_id"]
    return r


# ---------------------------------------------------------------------------
# catalog & knowledge base
# ---------------------------------------------------------------------------

def test_registry_scale(state):
    reg = state["registry"]
    assert reg.count() >= 500, "brief requires 500+ tools"
    assert reg.implemented_count() >= 50
    names = [t.name for t in reg.all()]
    assert len(set(names)) == len(names), "tool names must be unique"


def test_knowledge_base_sections(state):
    sections = state["rag"].sections()
    assert len(sections) == 5, f"expected 5 sections, got {sections}"
    for name, n in sections.items():
        assert n >= 100, f"section {name} has {n} entries (<100)"
    assert state["rag"].count() >= 500


def test_business_db_seeded(state):
    stats = state["db"].stats()
    assert stats["users"] >= 200
    assert stats["invoices"] >= 300
    assert stats["disputes"] >= 50
    assert stats["transactions"] >= 500
    # task-brief guarantees
    assert state["db"].query_one("SELECT id FROM users WHERE id='user_123'")
    assert state["db"].query_one("SELECT id FROM disputes WHERE user_id='user_123' AND status='open'")


# ---------------------------------------------------------------------------
# retrieval quality
# ---------------------------------------------------------------------------

def test_rag_retrieval_policy_question(state):
    hits = state["rag"].hybrid_search("What is our data retention policy for transactions?", top_k=3)
    assert hits, "no hits returned"
    assert hits[0].section in ("Policies & Compliance", "Frequently Asked Questions")
    assert "retention" in hits[0].title.lower() or "retention" in hits[0].content.lower()


def test_rag_retrieval_api_question(state):
    hits = state["rag"].hybrid_search("POST /v2/invoices endpoint parameters", top_k=3)
    assert hits
    assert any(h.section == "API Reference" for h in hits[:3])


def test_router_funnel(state):
    route = state["router"].route("What was my total sales volume last month?")
    assert len(route.tools) <= 8, "LLM must never see more than ~8 tools"
    assert route.matched_domain == "Reporting & Analytics"
    assert any(t.name == "paypal.reports.get_sales_report" for t in route.tools)


# ---------------------------------------------------------------------------
# agent: exact task-brief examples
# ---------------------------------------------------------------------------

def test_invoice_send_chain(state):
    r = _chat(state, "Send an invoice for $50 to john@example.com")
    names = [t["name"] for t in r["tool_calls"]]
    assert "paypal.invoices.create_invoice" in names
    assert "paypal.invoices.send_invoice" in names
    assert all(t["ok"] for t in r["tool_calls"])
    assert "john@example.com" in r["reply"]
    assert "INV-" in r["reply"]


def test_sales_volume_last_month(state):
    r = _chat(state, "What was my total sales volume last month?")
    assert r["tool_calls"][0]["name"] == "paypal.reports.get_sales_report"
    data = r["tool_calls"][0]["result"]
    assert data["total_sales"] > 0
    assert "$" in r["reply"]


def test_dispute_open_user123(state):
    r = _chat(state, "Is there a dispute open from user_123?")
    assert r["tool_calls"][0]["name"] == "paypal.disputes.list_disputes"
    data = r["tool_calls"][0]["result"]
    assert data["count"] >= 1
    assert all(d["status"] == "open" for d in data["disputes"])
    assert "DSP-" in r["reply"]


def test_system_search_tools(state):
    r = _chat(state, "What tools are available for managing invoices?")
    assert r["tool_calls"][0]["name"] == "system.search_capabilities"
    tools = r["tool_calls"][0]["result"]["tools"]
    assert len(tools) >= 3
    assert all("invoice" in t["name"] for t in tools[:3])


def test_last_request_status(state):
    _chat(state, "List my invoices")
    r = _chat(state, "What's the status of my last request?")
    assert r["tool_calls"][0]["name"] == "system.get_last_request"
    assert r["tool_calls"][0]["result"]["tool"] == "paypal.invoices.list_invoices"
    assert "success" in r["reply"]


def test_rag_knowledge_question(state):
    r = _chat(state, "How long do I have to respond to a dispute?")
    assert r["tool_calls"][0]["name"] == "system.ask_knowledge_base"
    assert r["sources"], "RAG sources must be surfaced"
    assert "knowledge base" in r["reply"].lower()


def test_fx_conversion(state):
    r = _chat(state, "What is the exchange rate from USD to INR?")
    assert r["tool_calls"][0]["name"] == "paypal.fx.get_exchange_rate"
    data = r["tool_calls"][0]["result"]
    assert data["base"] == "USD" and data["quote"] == "INR"
    assert data["rate"] > 1


# ---------------------------------------------------------------------------
# error handling & edge cases
# ---------------------------------------------------------------------------

def test_missing_param_clarification(state):
    r = _chat(state, "Cancel my invoice")
    assert not r["tool_calls"][0]["ok"]
    assert "invoice" in r["reply"].lower() or "provide" in r["reply"].lower()


def test_not_found_error(state):
    r = _chat(state, "Show me invoice INV-9999")
    assert not r["tool_calls"][0]["ok"]
    assert "not found" in r["reply"].lower() or "not found" in (r["tool_calls"][0].get("error") or "")


def test_simulated_tool_flagged(state):
    r = _chat(state, "List payout batches")
    assert r["tool_calls"], "a payout tool should be selected"
    tc = r["tool_calls"][0]
    if tc["name"].startswith("datazoic."):
        assert tc["simulated"] is True


def test_tracing_records_events(state):
    sid = state["ctx"]["session_holder"].session_id
    events = state["tracer"].trace(sid)
    types = {e["type"] for e in events}
    assert "route" in types and "tool_call" in types and "answer" in types
