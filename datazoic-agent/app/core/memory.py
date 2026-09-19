"""Session state management.

State is a plain JSON document per session persisted in SQLite (state.db),
so sessions survive process restarts. The document holds:

    messages        – chat history (last 30 turns kept)
    tool_calls      – every tool executed in the session (with results)
    last_tool_call  – the most recent one (feeds `system.get_last_request`)

In production this moves to Redis/Postgres behind the same interface; the
document shape is what the agent reasons over, not the storage.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


class MemoryStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, data TEXT NOT NULL, updated_at REAL NOT NULL)"
        )
        self.conn.commit()

    def _load(self, sid: str) -> Optional[Dict]:
        row = self.conn.execute("SELECT data FROM sessions WHERE session_id=?", (sid,)).fetchone()
        return json.loads(row[0]) if row else None

    def get_or_create(self, sid: Optional[str]) -> str:
        if sid:
            if self._load(sid) is not None:
                return sid
        sid = uuid.uuid4().hex[:12]
        self.save(sid, {
            "messages": [],
            "tool_calls": [],
            "last_tool_call": None,
            "created_at": time.time(),
        })
        return sid

    def get(self, sid: str) -> Dict:
        data = self._load(sid)
        if data is None:
            data = {"messages": [], "tool_calls": [], "last_tool_call": None, "created_at": time.time()}
            self.save(sid, data)
        return data

    def save(self, sid: str, data: Dict) -> None:
        self.conn.execute(
            "INSERT INTO sessions (session_id, data, updated_at) VALUES (?,?,?)"
            " ON CONFLICT(session_id) DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at",
            (sid, json.dumps(data, default=str), time.time()),
        )
        self.conn.commit()

    def append_message(self, sid: str, role: str, content: str) -> None:
        data = self.get(sid)
        data["messages"].append({"role": role, "content": content, "at": time.time()})
        data["messages"] = data["messages"][-30:]
        self.save(sid, data)

    def record_tool_call(self, sid: str, tool: str, args: Dict, result_dict: Dict) -> None:
        data = self.get(sid)
        entry = {
            "tool": tool,
            "args": args,
            "ok": result_dict.get("ok"),
            "ms": result_dict.get("ms"),
            "at": time.time(),
            "data": _trim(result_dict.get("data")),
        }
        data["tool_calls"].append(entry)
        data["tool_calls"] = data["tool_calls"][-40:]
        data["last_tool_call"] = entry
        self.save(sid, data)

    def last_request(self, sid: str) -> Optional[Dict]:
        data = self._load(sid)
        if not data or not data.get("last_tool_call"):
            return None
        e = data["last_tool_call"]
        return {
            "tool": e.get("tool"), "args": e.get("args"), "ok": e.get("ok"),
            "ms": e.get("ms"), "at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(e.get("at", 0))),
            "data": e.get("data"),
        }


def _trim(v: Any, limit: int = 1500):
    s = v if isinstance(v, str) else json.dumps(v, default=str)
    s = " ".join(s.split())
    return s[:limit] + ("…" if len(s) > limit else "")
