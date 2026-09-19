# Datazoic Agentic AI Platform — Scalable Agent Prototype

A professional-grade prototype that answers the Datazoic task brief: **how do you build a
robust agentic system when you have 100+ (even 1000s of) tools, without LLM accuracy
degrading?**

This repository is a **working, runnable system** implementing that design, plus the
required RAG pipeline tool and system-search tool, a chat UI, a REST API, an
observability trail, and a full test suite.

```
┌────────────┐     ┌─────────────┐     ┌─────────────────────────────────────────────┐
│  Chat UI   │────▶│ FastAPI     │────▶│                 AGENT                        │
│ (static/   │     │ REST /api/* │     │  ┌──────────┐   ┌──────────────────────────┐ │
│ index.html)│◀────│  SSE-free   │◀────│  │  Router  │──▶│ ≤ 8 tools in LLM context │ │
└────────────┘     └─────────────┘     │  │ 2-level  │   │ (from a 500+ tool catalog)│ │
                                       │  └──────────┘   └────────────┬─────────────┘ │
                                       │        plan → act → observe loop (≤ N steps) │
                                       └──────────────────────────────┼────────────────┘
                                     ┌──────────────────┬─────────────┼──────────────┬───────────────┐
                                     ▼                  ▼             ▼              ▼               ▼
                              ┌────────────┐   ┌──────────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────┐
                              │ Business DB│   │ RAG vector   │ │ Business │ │ System    │ │  Memory +    │
                              │ (SQLite)   │   │ store (SQLite│ │ tools    │ │ tools     │ │  Tracer      │
                              │ 2,200+ rows│   │ 608 docs/5sec│ │ (443 sim)│ │ (3 meta)  │ │  (SQLite)    │
                              └────────────┘   └──────────────┘ └──────────┘ └───────────┘ └──────────────┘
```

## Quickstart

```bash
cd datazoic-agent
pip install -r requirements.txt

# everything is auto-built on first start (docs -> RAG store, seed -> business DB)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open the chat UI at `http://localhost:8000/` (Swagger at `/docs`).

### Explicit build steps (optional)

```bash
python scripts/generate_knowledge_base.py   # 5 section docs, 100+ entries each (608 total)
python scripts/build_rag_db.py              # chunk + embed -> data/vector_store/rag.db
python scripts/seed_business_db.py          # 12 months of deterministic business data
```

### Run the tests

```bash
pytest tests/ -q        # 17 tests: catalog scale, KB sections, retrieval, agent loop
```

## The example queries from the brief, working

| You type | What the agent does |
|---|---|
| "Send an invoice for $50 to john@example.com" | Chained tool calls: `create_invoice` → `send_invoice` (ID passed between steps), invoice row written to SQLite |
| "What was my total sales volume last month?" | `get_sales_report` → SQL aggregate over `transactions`, answered with real numbers |
| "Is there a dispute open from user_123?" | `list_disputes(user_123, open)` → real dispute rows |
| "What tools are available for managing invoices?" | **System-search tool** → semantic search over the 500+ tool catalog |
| "What's the status of my last request?" | **System-search tool** → session memory of the last tool call |
| "How long do I have to respond to a dispute?" | **RAG tool** → hybrid (vector + BM25) retrieval over the knowledge base, answer with cited sources |
| "What is the exchange rate from USD to INR?" | `get_exchange_rate` → real rate table |

## The core design: two-level tool routing

The task's central problem: attaching every tool to the LLM degrades accuracy.
This system guarantees the planner **never sees more than 8 tools per turn**,
regardless of catalog size:

1. **Level 1 — Domain routing.** The query is embedded and scored against ~30
   domain descriptions; the top-3 domains become the candidate pool.
2. **Level 2 — Tool retrieval.** Inside those domains, each tool is scored
   `0.4·cosine(embedding) + 0.6·lexical-overlap` (precomputed at startup);
   the top-5 tools join 3 standing tools (RAG, capability search, last-request).

Cost per query is one matrix-vector multiply + set intersections — the same
machinery scales to 10k tools by swapping in an ANN index (see DESIGN.md).

## What's real vs simulated (honest prototype)

* **Real (implemented, 60 tools):** invoices, payments, disputes, reports,
  customers, webhooks, FX, tickets, fraud scoring — all read/write the SQLite
  business DB; RAG retrieval over the 608-document store; system self-search.
* **Simulated (443 tools):** the long tail of the 500+ catalog executes in a
  deterministic simulator (pure function of tool+args, clearly flagged in the
  UI and responses). The routing machinery is identical — the point of the
  catalog is the *scale problem*, not 500 backends.

## Knowledge base (RAG database)

Five sections, **each with 100+ entries** (608 total), built from document
files in `data/docs/` and stored in `data/vector_store/rag.db`:

| Section file | Section | Entries |
|---|---|---|
| `product_docs.md` | Product Documentation | 126 |
| `guides.md` | Step-by-Step Guides | 126 |
| `api_reference.md` | API Reference | 115 |
| `policies.md` | Policies & Compliance | 115 |
| `faq.md` | Frequently Asked Questions | 126 |

Retrieval is **hybrid**: signed feature-hashing embeddings (256-d, offline,
no model download) blended with pure-Python BM25 — strong both for semantic
phrasing and for identifiers/paths. The `Embedder` interface lets you drop in
`sentence-transformers` in production without touching retrieval code.

## API

| Endpoint | Purpose |
|---|---|
| `POST /api/chat` | `{message, session_id?}` → reply + full trace + routing + RAG sources |
| `POST /api/rag/search` | Direct hybrid retrieval over the knowledge base |
| `GET /api/tools?domain=&q=` | Browse/filter the 500+ tool catalog |
| `GET /api/stats` | Tool counts, KB sections, business-DB row counts |
| `GET /api/traces/{session_id}` | Observability event trail |
| `GET /api/sessions` | Session store summary |
| `GET /health` | Liveness + bootstrap info |

## Configuration

See `.env.example`. Highlights:

* `LLM_PROVIDER=auto|openai|heuristic` — with no API key the **heuristic
  planner** runs the same plan/act/observe loop offline (zero dependencies,
  reproducible, CI-safe). With `LLM_API_KEY` (or `OPENAI_API_KEY`) it switches
  to any OpenAI-compatible endpoint using native function calling.
* `TOP_K_TOOLS`, `TOP_K_DOMAINS`, `MAX_AGENT_STEPS` — the routing funnel and loop bounds.

## Project layout

```
app/
  main.py               FastAPI app + bootstrap wiring
  config.py             all settings (env-driven)
  state.py              process-wide state
  api/routes.py         REST endpoints
  core/
    router.py           ★ two-level tool router (the scale answer)
    agent.py            plan → act → observe loop, arg-refs for tool chains
    llm.py              HeuristicLLM (offline) + OpenAICompatLLM (API)
    memory.py           session state (SQLite-persisted)
    tracer.py           per-session observability events
  tools/
    registry.py         tool catalog + routing domains
    generator.py        60 core + 443 bulk tools (500+ catalog)
    implementations.py  real handlers over the business DB
    executor.py         validation + dispatch + error wrapping + simulator
  rag/
    embedder.py         offline 256-d hashing embeddings (swappable)
    vector_store.py     SQLite vector store + BM25 hybrid retrieval
    pipeline.py         markdown → chunks → store
  db/
    database.py         business SQLite schema + access
    seed.py             deterministic 12-month seed data
scripts/
  generate_knowledge_base.py   5 sections × 100+ entries
  build_rag_db.py              chunk + embed
  seed_business_db.py          business data seed
static/index.html     chat UI with live agent-trace panel
tests/test_agent.py   17 end-to-end tests
data/                 docs/, vector_store/rag.db, business.db, state.db, tools_registry.json
DESIGN.md             architecture write-up: choices, trade-offs, scaling path
```
