"""Application configuration.

All paths are anchored to the project root so the app works from any CWD.
Override via environment variables (see .env.example).
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("DATAZOIC_DATA_DIR", str(PROJECT_ROOT / "data")))
DOCS_DIR = DATA_DIR / "docs"                      # source markdown documents for RAG
BUSINESS_DB_PATH = DATA_DIR / "business.db"       # SQLite business database
RAG_DB_PATH = DATA_DIR / "vector_store" / "rag.db"  # SQLite-backed vector store
STATE_DB_PATH = DATA_DIR / "state.db"             # session state persistence
STATIC_DIR = PROJECT_ROOT / "static"


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


# --- LLM ---------------------------------------------------------------
# provider: auto | openai | heuristic
#   auto       -> openai if LLM_API_KEY/OPENAI_API_KEY is set, else heuristic
#   openai     -> OpenAI-compatible /chat/completions endpoint
#   heuristic  -> deterministic offline planner (zero dependencies, CI-safe)
LLM_PROVIDER = _env("LLM_PROVIDER", "auto").lower()
LLM_API_KEY = _env("LLM_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
LLM_BASE_URL = _env("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
LLM_MODEL = _env("LLM_MODEL", "gpt-4o-mini")
LLM_TIMEOUT_S = float(_env("LLM_TIMEOUT_S", "60"))

# --- Agent behaviour -----------------------------------------------------
MAX_AGENT_STEPS = int(_env("MAX_AGENT_STEPS", "4"))   # tool-loop iterations
TOP_K_TOOLS = int(_env("TOP_K_TOOLS", "5"))           # tools surfaced to the LLM per turn
TOP_K_DOMAINS = int(_env("TOP_K_DOMAINS", "3"))       # domains considered by the router
RAG_TOP_K = int(_env("RAG_TOP_K", "4"))               # KB chunks retrieved per RAG call
RAG_VECTOR_WEIGHT = float(_env("RAG_VECTOR_WEIGHT", "0.65"))

# --- Business DB ---------------------------------------------------------
SEED_DB_ON_START = _env("SEED_DB_ON_START", "1") == "1"
BUILD_RAG_ON_START = _env("BUILD_RAG_ON_START", "1") == "1"
