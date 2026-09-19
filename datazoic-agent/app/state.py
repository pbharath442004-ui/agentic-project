"""Process-wide application state (filled during FastAPI lifespan startup)."""
from __future__ import annotations

STATE: dict = {}
