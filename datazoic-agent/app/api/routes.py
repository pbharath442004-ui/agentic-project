"""REST API routes."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .. import config
from ..state import STATE

api_router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    llm: str
    steps: List[Dict[str, Any]]
    routing: Dict[str, Any]
    sources: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]


class RAGSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=800)
    top_k: int = Field(5, ge=1, le=20)
    section: Optional[str] = None


@api_router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> Dict[str, Any]:
    """Main agent endpoint: natural language -> routed tool execution -> answer."""
    agent = STATE.get("agent")
    if agent is None:
        raise HTTPException(503, "Agent is still booting.")
    holder = STATE["ctx"].get("session_holder")
    if holder is not None:
        holder.session_id = req.session_id  # meta tools (last_request) need the session
    return agent.chat(req.message, req.session_id)


@api_router.post("/rag/search")
def rag_search(req: RAGSearchRequest) -> Dict[str, Any]:
    """Direct access to the RAG pipeline (the same retrieval the RAG tool uses)."""
    rag = STATE.get("rag")
    if rag is None:
        raise HTTPException(503, "RAG store is still booting.")
    hits = rag.hybrid_search(req.query, top_k=req.top_k,
                             vector_weight=config.RAG_VECTOR_WEIGHT, section=req.section)
    return {
        "query": req.query,
        "count": len(hits),
        "results": [
            {"id": h.id, "section": h.section, "title": h.title,
             "score": round(h.score, 4), "vector_score": round(h.vector_score, 4),
             "bm25_score": round(h.bm25_score, 4), "snippet": h.snippet(400),
             "metadata": h.metadata}
            for h in hits
        ],
    }


@api_router.get("/tools")
def list_tools(domain: Optional[str] = None, q: Optional[str] = None,
               limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """Browse the tool catalog (this is also what `system.search_capabilities` returns)."""
    registry = STATE.get("registry")
    if registry is None:
        raise HTTPException(503, "Registry is still booting.")
    tools = registry.all()
    if domain:
        tools = [t for t in tools if t.domain.lower() == domain.lower()]
    if q:
        ql = q.lower()
        tools = [t for t in tools if ql in t.name or ql in t.description.lower()]
    total = len(tools)
    page = tools[offset:offset + min(limit, 200)]
    return {
        "total": total,
        "limit": limit, "offset": offset,
        "domains": {d: len(v) for d, v in sorted(registry.domains().items())},
        "tools": [
            {"name": t.name, "domain": t.domain, "service": t.service,
             "description": t.description, "implemented": t.implemented,
             "parameters": list(t.parameters.keys())}
            for t in page
        ],
    }


@api_router.get("/stats")
def stats() -> Dict[str, Any]:
    """Platform counters: tools, knowledge-base sections, business DB rows."""
    if not STATE:
        raise HTTPException(503, "Still booting.")
    return {
        "llm": STATE["llm"].provider,
        "tools": {
            "total": STATE["registry"].count(),
            "implemented": STATE["registry"].implemented_count(),
            "simulated": STATE["registry"].count() - STATE["registry"].implemented_count(),
            "domains": len(STATE["registry"].domains()),
        },
        "rag": {
            "documents": STATE["rag"].count(),
            "sections": STATE["rag"].sections(),
        },
        "business_db": STATE["db"].stats(),
        "agent": {"max_steps": config.MAX_AGENT_STEPS, "top_k_tools": config.TOP_K_TOOLS},
        "bootstrap_ms": STATE.get("bootstrap_ms"),
    }


@api_router.get("/traces/{session_id}")
def trace(session_id: str) -> Dict[str, Any]:
    """Observability: the event trail of an agent session."""
    if not STATE:
        raise HTTPException(503, "Still booting.")
    return {"session_id": session_id, "events": STATE["tracer"].trace(session_id)}


@api_router.get("/sessions")
def sessions() -> Dict[str, Any]:
    """Session store summary (state management visibility)."""
    if not STATE:
        raise HTTPException(503, "Still booting.")
    rows = STATE["memory"].conn.execute(
        "SELECT session_id, updated_at FROM sessions ORDER BY updated_at DESC LIMIT 20"
    ).fetchall()
    return {"sessions": [{"session_id": r[0], "updated_at": r[1]} for r in rows]}
