"""Observability: an in-memory event ring buffer per session.

Every agent turn emits typed events (route, tool_call, answer) — the same
events the chat API returns inline. The tracer keeps a history so you can
audit *why* the agent chose what it chose (which domains were scored,
which tools were retrieved, how long each step took). In production this
is where LangSmith/OpenTelemetry-style tracing plugs in.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any, Dict, List


class Tracer:
    def __init__(self, maxlen: int = 500):
        self._buf: Dict[str, deque] = defaultdict(lambda: deque(maxlen=maxlen))

    def event(self, session_id: str, type_: str, data: Dict[str, Any]) -> None:
        self._buf[session_id].append({
            "ts": time.time(),
            "type": type_,
            "data": data,
        })

    def trace(self, session_id: str) -> List[Dict[str, Any]]:
        return list(self._buf.get(session_id, []))

    def sessions(self) -> List[str]:
        return list(self._buf.keys())
