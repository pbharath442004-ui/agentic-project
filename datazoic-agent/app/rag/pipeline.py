"""RAG ingestion pipeline: markdown documents -> hybrid vector store.

Each `## Heading` block in a source document becomes one retrievable
knowledge entry with metadata (section, source file, entry id).  This keeps
chunks semantically atomic (one concept per chunk) which is the difference
between "RAG that answers" and "RAG that cites random paragraphs".

Sections of the sample knowledge base (each generated with 100+ entries):

    product_docs    -> Product Documentation
    guides          -> Step-by-Step Guides
    api_reference   -> API Reference
    policies        -> Policies & Compliance
    faq             -> Frequently Asked Questions
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

from .vector_store import Document, VectorStore

SECTION_LABELS = {
    "product_docs": "Product Documentation",
    "guides": "Step-by-Step Guides",
    "api_reference": "API Reference",
    "policies": "Policies & Compliance",
    "faq": "Frequently Asked Questions",
}

_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def parse_markdown(path: Path, section_key: str) -> List[Document]:
    """Split a markdown file into one Document per `## ` section."""
    text = path.read_text(encoding="utf-8")
    section_label = SECTION_LABELS.get(section_key, section_key)
    matches = list(_HEADING_RE.finditer(text))
    docs: List[Document] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if not body:
            continue
        title = m.group(1).strip()
        entry_id = re.sub(r"[^A-Za-z0-9-]+", "-", title)[:80].strip("-").lower() or f"doc-{i:03d}"
        docs.append(
            Document(
                id=f"{section_key}:{entry_id}",
                section=section_label,
                title=title,
                content=body,
                metadata={"section_key": section_key, "source_file": path.name, "entry_no": i + 1},
            )
        )
    return docs


def build_knowledge_base(docs_dir: str | Path, store: VectorStore) -> Dict[str, int]:
    """Parse every known section file in `docs_dir` and replace the store."""
    docs_dir = Path(docs_dir)
    all_docs: List[Document] = []
    counts: Dict[str, int] = {}
    for section_key, label in SECTION_LABELS.items():
        path = docs_dir / f"{section_key}.md"
        if not path.exists():
            continue
        section_docs = parse_markdown(path, section_key)
        counts[label] = len(section_docs)
        all_docs.extend(section_docs)
    if all_docs:
        store.replace_all(all_docs)
    return counts


def ensure_knowledge_base(docs_dir: str | Path, store: VectorStore) -> Dict[str, int]:
    """Load existing store; rebuild from documents only if the store is empty."""
    if store.count() == 0:
        return build_knowledge_base(docs_dir, store)
    return store.sections()
