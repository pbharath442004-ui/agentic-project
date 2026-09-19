"""Tool execution: schema validation, dispatch, error wrapping, timing.

Validation is deliberately small (types, required, enums) — in production
you'd run full JSON Schema validation. The point of the layer: every tool
failure becomes a structured `ToolResult` the agent can reason over
(clarify, retry, or report) instead of an exception killing the request.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .base import Tool, ToolResult
from .generator import build_catalog
from .implementations import HANDLERS, ToolError, dispatch
from .registry import Registry

ENUM_TYPES = {"string", "integer", "number"}


class Simulator:
    """Deterministic mock execution for bulk tools (no live backend).

    Responses are pure functions of (tool, args) so repeated calls are
    stable — useful for demos, tests and idempotency checks.
    """

    def run(self, tool: Tool, args: Dict) -> Dict[str, Any]:
        h = int(hashlib.md5(f"{tool.name}|{json.dumps(args, sort_keys=True, default=str)}".encode()).hexdigest()[:8], 16)
        ref = f"{tool.group[:3].upper()}-{h:06X}"
        status = "succeeded" if h % 7 else "pending"
        return {
            "id": ref,
            "status": status,
            "processed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "input_echo": args,
            "result_summary": f"{tool.name} completed ({status}) for the given parameters.",
        }


class ToolExecutor:
    def __init__(self, registry: Registry, ctx: Dict, simulator: Optional[Simulator] = None):
        self.registry = registry
        self.ctx = ctx
        self.simulator = simulator or Simulator()

    # -- validation --------------------------------------------------------
    @staticmethod
    def validate(tool: Tool, args: Dict):
        """Return (missing, invalid) parameter lists."""
        missing, invalid = [], []
        for pname, spec in tool.parameters.items():
            value = args.get(pname)
            if spec.get("required") and value in (None, ""):
                missing.append(pname)
                continue
            if value in (None, ""):
                continue
            ptype = spec.get("type", "string")
            if ptype in ("number", "integer"):
                try:
                    v = float(value)
                    if ptype == "integer" and v != int(v):
                        raise ValueError
                except (TypeError, ValueError):
                    invalid.append(pname)
                    continue
            if "enum" in spec and value not in spec["enum"]:
                invalid.append(pname)
        return missing, invalid

    # -- execution -----------------------------------------------------------
    def execute(self, tool_name: str, args: Optional[Dict] = None) -> ToolResult:
        args = args or {}
        start = time.perf_counter()
        tool = self.registry.get(tool_name)
        if tool is None:
            return ToolResult(tool=tool_name, ok=False, error=f"Unknown tool '{tool_name}'.",
                              ms=(time.perf_counter() - start) * 1000)
        missing, invalid = self.validate(tool, args)
        if missing:
            hint = f" Please provide: {', '.join(missing)}."
            return ToolResult(tool=tool.name, ok=False,
                              error=f"Missing required parameter(s): {', '.join(missing)}." + hint,
                              missing_params=missing,
                              ms=(time.perf_counter() - start) * 1000)
        if invalid:
            return ToolResult(tool=tool.name, ok=False,
                              error=f"Invalid value for parameter(s): {', '.join(invalid)}.",
                              ms=(time.perf_counter() - start) * 1000)
        try:
            if tool.handler == "simulated":
                data = self.simulator.run(tool, args)
                return ToolResult(tool=tool.name, ok=True, data=data, simulated=True,
                                  ms=(time.perf_counter() - start) * 1000)
            if tool.handler.startswith("db:"):
                data = dispatch(tool.handler, args, self.ctx)
                return ToolResult(tool=tool.name, ok=True, data=data,
                                  ms=(time.perf_counter() - start) * 1000)
            if tool.handler.startswith("system:") or tool.handler.startswith("rag:"):
                data = self._meta(tool.handler, args)
                return ToolResult(tool=tool.name, ok=True, data=data,
                                  ms=(time.perf_counter() - start) * 1000)
            return ToolResult(tool=tool.name, ok=False,
                              error=f"Unsupported handler '{tool.handler}'.",
                              ms=(time.perf_counter() - start) * 1000)
        except ToolError as e:
            return ToolResult(tool=tool.name, ok=False, error=e.message,
                              missing_params=e.missing,
                              ms=(time.perf_counter() - start) * 1000)
        except Exception as e:  # noqa: BLE001 - tool errors must never crash the agent
            return ToolResult(tool=tool.name, ok=False,
                              error=f"Tool execution error: {e.__class__.__name__}: {e}",
                              ms=(time.perf_counter() - start) * 1000)

    def _meta(self, handler: str, args: Dict) -> Any:
        kind, name = handler.split(":", 1)
        if kind == "system":
            if name == "search_capabilities":
                return self.ctx["registry_search"](args.get("query", ""), k=10)
            if name == "get_last_request":
                return self.ctx["last_request"]()
        elif kind == "rag":
            if name == "ask_knowledge_base":
                return self.ctx["rag_search"](args.get("query", ""), k=4)
        raise ToolError(f"Unsupported meta handler {handler}.", code="not_implemented")
