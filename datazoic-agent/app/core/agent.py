"""The agent: plan -> act -> observe loop.

Per user message:
  1. ROUT   – router selects <= TOP_K_TOOLS domain tools + standing tools.
  2. PLAN   – LLM picks tool call(s) (possibly a chained sequence with
              arg-refs between steps) or answers directly.
  3. ACT    – executor validates + runs each call; results feed back.
  4. OBSERVE– LLM either composes the final answer or issues the next
              tool step (bounded by MAX_AGENT_STEPS).
  5. MEM    – session state (messages, tool history) persisted.

Errors never crash the loop: tool failures become observations the LLM
can explain to the user or recover from (clarification, alternate tool).
"""
from __future__ import annotations

import re
import time
import uuid
from typing import Any, Dict, List, Optional

from ..config import MAX_AGENT_STEPS
from .llm import HeuristicLLM, OpenAICompatLLM, LLMResult
from .memory import MemoryStore
from .router import ToolRouter
from .tracer import Tracer
from ..tools.executor import ToolExecutor


def _resolve_arg_refs(tool_calls: List, observations: List[Dict]) -> List[Dict]:
    """Resolve placeholders like 'result:0.invoice_id' against prior results."""
    out = []
    for tc in tool_calls:
        args = dict(tc.args)
        for key, ref in list(tc.arg_refs.items()):
            m = re.match(r"result:(\d+)\.(.+)", ref)
            if not m:
                continue
            idx = int(m.group(1))
            path = m.group(2).split(".")
            if idx < len(observations):
                val = observations[idx]["result"].data
                for p in path:
                    if isinstance(val, dict) and p in val:
                        val = val[p]
                    else:
                        val = None
                        break
                if val is not None:
                    args[key] = val
        out.append({"name": tc.name, "args": args})
    return out


class Agent:
    def __init__(self, llm: HeuristicLLM | OpenAICompatLLM, router: ToolRouter,
                 executor: ToolExecutor, memory: MemoryStore, tracer: Tracer):
        self.llm = llm
        self.router = router
        self.executor = executor
        self.memory = memory
        self.tracer = tracer

    def chat(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        sid = self.memory.get_or_create(session_id)
        session = self.memory.get(sid)
        events: List[Dict[str, Any]] = []

        def ev(type_: str, data: Dict[str, Any]) -> None:
            entry = {"ts": round(time.time(), 3), "type": type_, "data": data}
            events.append(entry)
            self.tracer.event(sid, type_, entry)

        t0 = time.perf_counter()

        # 1) route ---------------------------------------------------------
        route = self.router.route(message)
        route_summary = route.summary()
        route_summary["total_tools_in_registry"] = self.router.registry.count()
        ev("route", route_summary)

        specs = [t.spec() for t in route.tools]
        all_observations: List[Dict[str, Any]] = []

        # 2) plan ----------------------------------------------------------
        plan = self.llm.plan(message, specs, session)
        ev("llm_plan", {"provider": self.llm.provider,
                        "tool_calls": [tc.name for tc in (plan.tool_calls or [])],
                        "direct_answer": plan.content is not None})

        # 3+4) act/observe loop ---------------------------------------------
        pending: List = plan.tool_calls or []
        steps = 0
        while pending and steps < MAX_AGENT_STEPS:
            steps += 1
            # resolve arg-refs sequentially: a later call in the batch may
            # reference the result of an earlier one (e.g. send_invoice using
            # the ID returned by create_invoice)
            local_obs = list(all_observations)
            executed = []
            for i, tc in enumerate(pending):
                call = _resolve_arg_refs([tc], local_obs)[0]
                result = self.executor.execute(call["name"], call["args"])
                rd = result.to_dict()
                obs_entry = {"call_index": i, "tool": call["name"],
                             "args": call["args"], "result": result,
                             "name": call["name"]}
                local_obs.append(obs_entry)
                all_observations.append(obs_entry)
                executed.append({"name": call["name"], "args": call["args"]})
                self.memory.record_tool_call(sid, call["name"], call["args"], rd)
                ev("tool_call", {"name": call["name"], "args": call["args"],
                                 "ok": result.ok, "ms": round(result.ms, 1),
                                 "simulated": result.simulated,
                                 "error": result.error,
                                 "result_preview": _preview(rd.get("data"))})
            session = self.memory.get(sid)
            session["_pending_calls"] = executed
            self.memory.save(sid, session)
            plan = self.llm.observe(message, specs, session, all_observations)
            pending = plan.tool_calls
            if pending:
                ev("llm_continue", {"tool_calls": [tc.name for tc in pending]})

        reply = plan.content or "Done."

        # sources for the UI (RAG hits) -------------------------------------
        sources = []
        for obs in all_observations:
            if obs["tool"] == "system.ask_knowledge_base" and obs["result"].ok:
                for s in obs["result"].data.get("sources", []):
                    sources.append({
                        "title": s.get("title"), "section": s.get("section"),
                        "score": round(s.get("score", 0.0), 4),
                        "snippet": s.get("snippet"),
                    })

        self.memory.append_message(sid, "user", message)
        self.memory.append_message(sid, "assistant", reply)
        ev("answer", {"reply": reply, "steps": steps, "total_ms": round((time.perf_counter() - t0) * 1000, 1)})

        return {
            "session_id": sid,
            "reply": reply,
            "llm": self.llm.provider,
            "steps": events,
            "routing": route_summary,
            "sources": sources,
            "tool_calls": [
                {"name": o["tool"], "args": o["args"], "ok": o["result"].ok,
                 "ms": round(o["result"].ms, 1), "simulated": o["result"].simulated,
                 "error": o["result"].error, "result": o["result"].data}
                for o in all_observations
            ],
        }


def _preview(data: Any, limit: int = 600) -> Any:
    import json
    if data is None:
        return None
    s = data if isinstance(data, str) else json.dumps(data, default=str)
    s = " ".join(s.split())
    return s[:limit] + ("…" if len(s) > limit else "")
