# Design Document — Scalable Agentic System

> Response to the Datazoic brief: *design a robust agentic system for 100+ tools,
> scalable to thousands, where LLM accuracy does not degrade as the tool count grows.*
> This document explains the architecture implemented in this repository, the choices
> made, and the trade-offs considered.

## 1. Problem framing

Tool-calling accuracy is a function of context. Empirically and architecturally, three
failure modes appear as tools are added to a single prompt:

1. **Selection confusion** — the model picks the wrong tool among near-synonyms
   (`list_payments` vs `get_payment_history` vs `datazoic.payouts.list_payout_batches`).
2. **Parameter hallucination** — schemas compete for attention; required arguments are
   dropped or invented.
3. **Instruction dilution** — system-prompt rules ("never invent IDs") lose weight as
   the tool block grows.

The design conclusion: **the set of tools the LLM sees must be a small, query-relevant
subset, selected by a retrieval mechanism — not a flat dump.** Everything else
(guardrails, state, observability) is secondary to that decision.

## 2. Architecture overview

```
User → Chat UI → FastAPI REST → Agent (plan/act/observe loop)
                                    │
                    ┌───────────────┼────────────────────┐
                    ▼               ▼                    ▼
             ToolRouter        Executor              Memory/Tracer
             (2-level)         (validate→dispatch)   (SQLite session state)
                    │               │
            domain tier     ┌───────┼────────┬──────────────┐
            tool tier       ▼       ▼        ▼              ▼
                        DB tools  RAG tool System tools  Simulator
                        (SQLite) (vector+BM25)(self-query)(deterministic)
```

* **Chat UI** — static HTML/JS, renders the reply *and* the full agent trace
  (routing scores, tool calls, retrieved sources). Transparency is a feature:
  every "why did the agent do that" is answerable from the trace.
* **FastAPI REST** — thin transport; `/api/chat` is the only stateful endpoint.
* **Agent** — a bounded plan→act→observe loop (ReAct-style) with argument
  references so one step can feed the next (`create_invoice` → `send_invoice`).
* **ToolRouter** — the core scale mechanism (below).
* **Executor** — schema validation, dispatch, deterministic simulator, error
  wrapping. Tool failures become *observations*, never crashes.
* **Memory / Tracer** — session document in SQLite + per-session event ring.

## 3. Tool selection & routing (the core)

### 3.1 Two-level funnel

* **Level 1 — domain routing.** ~30 routing domains ("Invoicing", "Payouts",
  "FX & Currencies", …), each with a short descriptive blurb. Query embedding vs
  domain blurb embeddings (plus a lexical term) → top-3 domains.
* **Level 2 — tool retrieval.** Inside candidate domains, each tool's
  `name + description` is embedded **once at startup**. Per query:
  `score = 0.4·cosine + 0.6·dice(lexical)`, top-5 tools.
* **Standing tools.** The three meta tools from the brief — RAG, capability
  search, last-request — are always present (they are the "index of indexes").

Result: **≤ 8 tools in the LLM context at any time, from a 503-tool catalog**
(the router summary returned in every response reports the funnel live).

### 3.2 Why hybrid (vector + lexical)

* Pure embeddings smear identifiers (`INV-0424`, `/v2/invoices`, error codes)
  and conflate near-synonym tool families — exactly the confusion we're fighting.
* Pure lexical retrieval fails on paraphrase ("bill me" ≠ "invoice").
* Dice-coefficient lexical overlap is precise, zero-cost, and needs no tuning;
  the 0.4/0.6 blend was chosen so an exact-term match (user quotes a tool name
  or ID) dominates while paraphrases still resolve.

### 3.3 Why the router is a separate layer (not an LLM call)

* **Latency/cost:** retrieval is a matrix multiply + set intersection —
  ~sub-millisecond — versus an LLM classification call per turn.
* **Determinism & testability:** routing is unit-testable without any model
  (the test suite asserts `matched_domain == "Reporting & Analytics"` for the
  sales query).
* **Failure independence:** if the LLM is down/degraded, retrieval still
  narrows the space; the heuristic planner can run it end-to-end offline.

## 4. Agent structure

* **Single planner, many tools** (not one sub-agent per domain). Sub-agents
  multiply context, state, and debugging surface; with a strong router they add
  little. If domains later need different policies (e.g., a finance domain with
  extra guardrails), the extension point is a *per-domain system prompt and
  tool policy* in the router — not a new agent process.
* **Bounded loop** (`MAX_AGENT_STEPS=4`) with explicit termination: the LLM
  either emits the final answer or the loop stops and the last observation is
  reported. No unbounded recursion.
* **Multi-step chains via arg-refs** (`result:0.invoice_id`): deterministic
  parameter passing between tool calls in the same batch — the model never has
  to "remember" an ID it saw one step ago.
* **LLM layer is pluggable.** `OpenAICompatLLM` (native function calling, any
  compatible endpoint) and `HeuristicLLM` (deterministic offline planner: intent
  classification → slot filling via regex → keyword scoring) implement the same
  `plan/observe` interface. The rest of the system is identical either way —
  which is why the demo, tests, and CI run with no API key at all.

## 5. The two special tools (per the brief)

* **RAG pipeline tool** (`system.ask_knowledge_base`): hybrid vector+BM25
  retrieval over the 608-entry, 5-section knowledge base (100+ per section).
  The answer is *composed from retrieved entries with citations*, not from
  model memory — the UI shows each source with its section and score.
* **System search tool** (`system.search_capabilities`, `system.get_last_request`):
  the agent can introspect its own catalog and session history — "what tools
  exist for invoices?" is answered by the *same retrieval used for routing*,
  and "status of my last request?" is answered from persisted session memory.

## 6. State management

* **Session document** (JSON in SQLite): messages, every tool call with result,
  `last_tool_call`. Plain serializable state survives restarts and is trivially
  migratable to Redis/Postgres behind the same interface.
* **Design rules:** (a) the LLM never holds state — it reads/writes through the
  agent; (b) observations are trimmed (≤1.5 KB per stored result) so sessions
  can't grow unbounded; (c) write-path tools are idempotency-friendly
  (create operations return stable IDs; the API contract documents
  `Idempotency-Key` support).
* **Why not a full state machine framework:** for a chat agent, an
  append-only observation log + last-N window covers 95% of cases; the
  remaining 5% (multi-day workflows) would want durable task state, which is a
  separate subsystem (job queue) rather than conversation state.

## 7. Error handling

Layered, with a single rule: **errors are data, not exceptions.**

1. **Validation** — required/enum/type checks *before* execution; failures
   return `missing_params` so the agent can ask the user (slot-filling loop),
   e.g. "Cancel my invoice" → "please provide the invoice ID".
2. **Execution** — every handler is wrapped; SQL/IO errors become structured
   `ToolResult.error` the planner explains to the user.
3. **Domain errors** — not-found, invalid-state transitions
   ("can't refund a failed payment") carry the reason so the answer is
   actionable, not apologetic.
4. **Loop safety** — step bound, retry-free by default (deterministic retry
   only for idempotent reads), full trace of every failure.

## 8. Scalability path (50 → 500 → 1000s of tools)

| Dimension | Now (prototype) | At 10k+ tools |
|---|---|---|
| Tool index | in-memory numpy (503×256 float32 ≈ 0.5 MB) | ANN (HNSW/pgvector/Qdrant) behind the same `route()` interface |
| Descriptions | embedded at startup, cached | versioned embedding cache; only changed tools re-embedded |
| Domains | 30 static blurbs | learned clustering over tool embeddings (periodic offline job) |
| Retrieval cost | O(tools) with tiny constants | O(log n) via ANN; lexical tier via inverted index |
| LLM context | ≤ 8 tools | unchanged — this is the invariant the design protects |
| Execution | single process, SQLite | per-service adapters (gRPC/HTTP), simulator as default for unimplemented |

The **invariant** is what matters: catalog growth never increases per-query
LLM context. A 5000-tool catalog routes exactly like the 503-tool one.

Other scale levers: response caching keyed on (query, tool, args-hash) for
read tools; horizontal FastAPI workers (state lives in SQLite→Postgres, so
workers are stateless); the trace system already emits OpenTelemetry-shaped
events.

## 9. Why this stack — choices & trade-offs

The brief invites frameworks (LangGraph, LangChain, LlamaIndex, CrewAI, DSPy).
I **built the core from scratch** (FastAPI + a ~300-line agent loop) for
deliberate reasons, and kept the seams where frameworks would slot in:

| Option | Pros | Cons | Verdict here |
|---|---|---|---|
| **From scratch (chosen)** | Every line is inspectable; the routing trick — the actual answer to the brief — is visible and testable; zero framework churn; smallest dependency surface; trivially CI-able offline | You own the loop, state, and tracing; no built-in eval harness | The brief's deliverable is a *design argument with a working model*; scratch maximizes signal. The LLM/memory/vector layers are interface-stable swap points. |
| **LangGraph** | Graph-based state machines, checkpointing, streaming; strong for multi-agent DAGs | Heavier abstraction; the 2-level routing would be one node hiding the interesting part; version churn in the LangChain ecosystem | Would use for durable multi-day workflows; overkill for a per-turn chat loop. |
| **LangChain** | Huge tool/library ecosystem | Abstraction layers obscure exactly the behavior the interview should demonstrate; less control over retrieval blending | Avoided; its retriever utilities are convenient but not the differentiator. |
| **LlamaIndex** | Best-in-class ingestion + retrieval (hybrid, reranking) | Library focus is RAG, not tool routing; same ecosystem churn | The RAG pipeline here mirrors its chunk→embed→retrieve pattern with a 200-line dependency-free store; a LlamaIndex node is a drop-in upgrade if corpus scale demands. |
| **CrewAI / DSPy** | Multi-agent role workflows / prompt optimization | Optimizes for agent-team patterns and prompt tuning — orthogonal to the tool-scale problem | Not applicable to this core problem. |
| **Observability (LangSmith etc.)** | Rich tracing/eval UI | External dependency, keys, data egress | The tracer emits the same event schema; a LangSmith/OpenTelemetry exporter is a ~20-line adapter (see `core/tracer.py`). |

**Embeddings:** signed feature hashing (256-d, deterministic, offline) instead
of a downloaded sentence-transformer model: zero network, reproducible, and —
combined with BM25 — strong on this keyword-dense corpus. The cost is weaker
pure-semantic recall, which the hybrid score compensates; the `Embedder`
interface is the upgrade path.

**Vector store:** SQLite + numpy instead of FAISS/pgvector: one process, no
service, 0.5 MB of vectors; the `hybrid_search()` interface is identical to
what a pgvector backend would expose, so the swap is mechanical, not
architectural.

## 10. Evaluation approach (how we'd prove accuracy doesn't degrade)

The prototype ships with a golden set (the 17 pytest cases encode the brief's
example queries plus edge cases: clarification, not-found, simulated-tool
flagging, tracing). For production-scale claims we'd add:

* **Routing precision@5** over a labeled query→tool set (report per domain).
* **End-to-end task success** on the golden set across catalog sizes
  (100 / 500 / 2000 tools) — the key experiment: accuracy flat while context
  stays ≤ 8 tools.
* **Clarification rate** (how often the agent must ask for a slot) as a UX
  metric, and **trace-based audit** sampling for drift.

## 11. Known limitations (honest list)

* The heuristic planner is regex/rule-based: it demos the architecture
  offline but a real LLM behind the same interface handles paraphrase better
  (swap via `LLM_API_KEY`).
* 443/503 tools are simulated by design (no live backends in a prototype);
  all 60 core tools are real against the business DB.
* Hashing embeddings + pure-Python BM25 are the lightweight tier; semantic
  recall on novel phrasing is good, not SOTA.
* Single-process state (SQLite) — fine for a prototype; the interfaces assume
  a shared store for horizontal scaling.
