"""Tool definition primitives."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Tool:
    """A single callable capability exposed to the agent.

    `handler` encodes where execution goes:
      * "rag"            -> RAG pipeline tool
      * "system"         -> system self-query tools
      * "db:<fn>"        -> implemented against the business SQLite DB
      * "simulated"      -> deterministic mock execution (no live backend)
    """
    name: str                      # e.g. "paypal.invoices.create_invoice"
    service: str                   # e.g. "paypal"
    group: str                     # e.g. "invoices"
    domain: str                    # routing domain, e.g. "Invoicing"
    description: str
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    handler: str = "simulated"
    implemented: bool = False

    def spec(self) -> Dict[str, Any]:
        """OpenAI-style function spec (works with any tools-capable LLM)."""
        props = {}
        required = []
        for pname, p in self.parameters.items():
            spec_p: Dict[str, Any] = {"type": p.get("type", "string"), "description": p.get("description", "")}
            if "enum" in p:
                spec_p["enum"] = p["enum"]
            props[pname] = spec_p
            if p.get("required"):
                required.append(pname)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": props,
                    "required": required,
                    "additionalProperties": False,
                },
            },
        }


@dataclass
class ToolResult:
    tool: str
    ok: bool
    data: Any = None
    error: Optional[str] = None
    missing_params: Optional[list] = None
    simulated: bool = False
    ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        out = {"tool": self.tool, "ok": self.ok, "ms": round(self.ms, 1)}
        if self.ok:
            out["data"] = self.data
            if self.simulated:
                out["note"] = "simulated execution (prototype; no live backend for this tool)"
        else:
            out["error"] = self.error
            if self.missing_params:
                out["missing_params"] = self.missing_params
        return out


def timed(fn):
    """Decorator recording execution time on the result via closure helper."""
    def wrapper(*a, **kw):
        start = time.perf_counter()
        result = fn(*a, **kw)
        result.ms = (time.perf_counter() - start) * 1000
        return result
    return wrapper
