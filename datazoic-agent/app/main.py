"""Datazoic Agentic AI Platform — FastAPI entry point.

Wires together: business DB, RAG vector store, tool registry (500+),
router, LLM (heuristic or OpenAI-compatible), memory, tracer, agent.

Startup is self-healing: if the RAG store or business DB is missing,
it (re)builds them from the bundled documents/seed data — so a fresh
clone runs with zero manual steps.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import config
from .api.routes import api_router
from .core.agent import Agent
from .core.llm import build_llm
from .core.memory import MemoryStore
from .core.router import ToolRouter
from .core.tracer import Tracer
from .db.database import BusinessDB
from .rag.pipeline import ensure_knowledge_base
from .rag.vector_store import VectorStore
from .tools.executor import ToolExecutor
from .tools.registry import Registry
from .state import STATE


def _bootstrap() -> dict:
    t0 = time.perf_counter()

    # business DB (auto-seed when empty)
    db = BusinessDB(config.BUSINESS_DB_PATH)
    if config.SEED_DB_ON_START and db.is_empty():
        from .db.seed import seed
        db_stats = seed(db)
        print(f"[bootstrap] seeded business DB: {db_stats}")

    # RAG vector store (auto-build from docs when empty)
    rag = VectorStore(config.RAG_DB_PATH)
    if config.BUILD_RAG_ON_START and rag.count() == 0:
        counts = ensure_knowledge_base(config.DOCS_DIR, rag)
        print(f"[bootstrap] built RAG store: {counts}")

    # tool registry
    from .tools.generator import build_catalog
    registry = Registry()
    tools = build_catalog()
    registry.register_many(tools)
    registry.dump_json(config.DATA_DIR / "tools_registry.json")
    print(f"[bootstrap] tool registry: {registry.count()} tools "
          f"({registry.implemented_count()} implemented, {registry.count() - registry.implemented_count()} simulated)")

    # memory + tracer
    memory = MemoryStore(config.STATE_DB_PATH)
    tracer = Tracer()

    def registry_search(query: str, k: int = 10):
        route = router.route(query)
        meta = {"system.ask_knowledge_base", "system.search_capabilities", "system.get_last_request"}
        tools_out = [
            {"name": t.name, "domain": t.domain, "description": t.description,
             "score": round(route.tool_scores.get(t.name, 0.0), 4)}
            for t in route.tools if t.name not in meta
        ][:k]
        return {"query": query, "tools": tools_out, "count": len(tools_out)}

    def last_request():
        sid = getattr(ctx_obj, "session_id", None)
        return memory.last_request(sid) if sid else None

    def rag_search(query: str, k: int = 4):
        hits = rag.hybrid_search(query, top_k=k, vector_weight=config.RAG_VECTOR_WEIGHT)
        sources = [
            {"id": h.id, "section": h.section, "title": h.title,
             "score": h.score, "snippet": h.snippet(300)}
            for h in hits
        ]
        return {"query": query, "sources": sources, "count": len(sources)}

    class _Ctx:  # tiny context holder so meta tools know the session
        session_id: str | None = None

    ctx_obj = _Ctx()
    ctx = {
        "db": db,
        "now": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        "registry_search": registry_search,
        "last_request": last_request,
        "rag_search": rag_search,
        "session_holder": ctx_obj,
    }

    router = ToolRouter(registry)
    executor = ToolExecutor(registry, ctx)
    llm = build_llm()
    agent = Agent(llm, router, executor, memory, tracer)

    return {
        "db": db, "rag": rag, "registry": registry, "router": router,
        "executor": executor, "llm": llm, "memory": memory, "tracer": tracer,
        "agent": agent, "ctx": ctx,
        "bootstrap_ms": round((time.perf_counter() - t0) * 1000, 1),
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    STATE.update(_bootstrap())
    yield
    STATE["db"].conn.close()
    STATE["rag"].conn.close()


app = FastAPI(
    title="Datazoic Agentic AI Platform",
    version="1.0.0",
    description=(
        "Scalable agentic system prototype: chat UI -> FastAPI -> agent router "
        "-> 500+ tools (hierarchical retrieval) + RAG knowledge base + system self-search."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health", tags=["system"])
def health():
    return {
        "status": "ok",
        "service": "datazoic-agent",
        "version": app.version,
        "llm": STATE.get("llm").provider if STATE.get("llm") else "booting",
        "tools": STATE.get("registry").count() if STATE.get("registry") else 0,
        "rag_documents": STATE.get("rag").count() if STATE.get("rag") else 0,
    }


# static chat UI (mounted last so /api/* and /health win)
app.mount("/", StaticFiles(directory=str(config.STATIC_DIR), html=True), name="ui")
