"""Build the RAG vector database from data/docs/*.md.

Usage:
    python scripts/build_rag_db.py

Output: data/vector_store/rag.db  (SQLite: documents + embeddings + BM25 index)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import DOCS_DIR, RAG_DB_PATH  # noqa: E402
from app.rag.pipeline import build_knowledge_base  # noqa: E402
from app.rag.vector_store import VectorStore  # noqa: E402


def main() -> int:
    if not DOCS_DIR.exists() or not list(DOCS_DIR.glob("*.md")):
        print("No documents found in data/docs — run scripts/generate_knowledge_base.py first.")
        return 1
    store = VectorStore(RAG_DB_PATH)
    counts = build_knowledge_base(DOCS_DIR, store)
    print("RAG database built at", RAG_DB_PATH)
    total = 0
    for section, n in sorted(counts.items()):
        print(f"  {section:<28} {n:4d} entries")
        total += n
        assert n >= 100, f"section '{section}' below the 100-entry minimum"
    print(f"  {'TOTAL':<28} {total:4d} entries")
    # smoke test the retrieval
    hits = store.hybrid_search("How long do I have to respond to a dispute?", top_k=3)
    print("\nRetrieval smoke test — 'How long do I have to respond to a dispute?':")
    for h in hits:
        print(f"  [{h.score:.3f}] ({h.section}) {h.title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
