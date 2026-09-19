"""Two-level tool router — the core answer to the 100+/1000+ tool problem.

LLM tool-calling accuracy degrades sharply as the tool list grows (the
task's core problem). This router guarantees the planner LLM sees at most
`TOP_K_TOOLS` (5) domain tools + 3 standing system tools per turn — even
with 500+ tools registered.

Level 1 — Domain routing:
    embed the query, score against ~30 domain descriptions, keep top-3.
Level 2 — Tool retrieval inside those domains:
    hybrid score = 0.4 * cosine(embedding) + 0.6 * dice(lexical overlap)
    between the query and each tool's `name + description`
    (precomputed at startup), keep top-5.

Why hybrid: embeddings give semantic recall ("bill me" ~ "invoice"),
lexical overlap gives precision on identifiers and exact terms. Both are
computed once per tool at startup, so per-query cost is a single matrix
multiply + set intersection — O(tools) with tiny constants, and it
parallelizes cleanly to thousands of tools (swap in ANN for 100k+).
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..config import TOP_K_DOMAINS, TOP_K_TOOLS
from ..rag.embedder import HashingEmbedder, tokenize
from ..tools.base import Tool
from ..tools.registry import DOMAINS, Registry

_STOP = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "do", "does", "did",
    "have", "has", "had", "will", "would", "could", "should", "may", "might", "shall", "can",
    "need", "to", "of", "in", "on", "for", "with", "about", "at", "by", "from", "as", "into",
    "and", "or", "but", "if", "then", "than", "so", "such", "my", "your", "our", "its", "it",
    "its", "there", "here", "what", "which", "who", "whom", "when", "where", "why", "how",
    "any", "some", "please", "me", "i", "you", "we", "they", "he", "she", "this", "that",
    "these", "those", "just", "only", "also", "was", "there", "a",
}

_STANDING_TOOLS = ["system.ask_knowledge_base", "system.search_capabilities", "system.get_last_request"]


def _dice(a: str, b: str) -> float:
    """Dice coefficient over non-stopword tokens (lexical similarity)."""
    ta = {t for t in tokenize(a) if t not in _STOP}
    tb = {t for t in tokenize(b) if t not in _STOP}
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    if inter == 0:
        # soft: partial token prefixes (e.g. 'invoice' vs 'invoices')
        inter = sum(1 for x in ta if any(y.startswith(x[:6]) or x.startswith(y[:6]) for y in tb))
    return (2.0 * inter) / (len(ta) + len(tb))


@dataclass
class RouteResult:
    tools: List[Tool] = field(default_factory=list)
    domain_scores: Dict[str, float] = field(default_factory=dict)
    tool_scores: Dict[str, float] = field(default_factory=dict)
    matched_domain: Optional[str] = None
    confidence: float = 0.0
    ms: float = 0.0

    def summary(self) -> Dict:
        return {
            "matched_domain": self.matched_domain,
            "domain_scores": {k: round(v, 4) for k, v in
                              sorted(self.domain_scores.items(), key=lambda x: -x[1])[:TOP_K_DOMAINS]},
            "selected_tools": [
                {"name": t.name, "domain": t.domain, "score": round(self.tool_scores.get(t.name, 0.0), 4),
                 "implemented": t.implemented}
                for t in self.tools
            ],
            "confidence": round(self.confidence, 4),
            "ms": round(self.ms, 1),
            "total_tools_in_registry": None,  # filled by caller
        }


class ToolRouter:
    def __init__(self, registry: Registry, dim: int = 256):
        self.registry = registry
        self.embedder = HashingEmbedder(dim)
        self._domain_names: List[str] = []
        self._domain_vectors: Optional[np.ndarray] = None
        self._tool_names: List[str] = []
        self._tool_vectors: Optional[np.ndarray] = None
        self._tool_lex: List[str] = []
        self._tool_domain: List[str] = []
        self._build_index()

    def _build_index(self) -> None:
        tools = self.registry.all()
        self._tool_names = [t.name for t in tools]
        self._tool_domain = [t.domain for t in tools]
        self._tool_lex = [f"{t.name.replace('.', ' ')} {t.description}" for t in tools]
        texts = self._tool_lex
        self._tool_vectors = self.embedder.embed_batch(texts) if texts else None
        self._domain_names = list(DOMAINS.keys())
        self._domain_vectors = self.embedder.embed_batch([f"{d}. {desc}" for d, desc in DOMAINS.items()])

    def route(self, query: str) -> RouteResult:
        start = time.perf_counter()
        res = RouteResult()
        qv = self.embedder.embed(query)

        # ---- Level 1: domains -------------------------------------------
        dom_scores = {}
        for i, d in enumerate(self._domain_names):
            cos = float(np.dot(self._domain_vectors[i], qv))
            lex = _dice(query, f"{d} {DOMAINS[d]}")
            dom_scores[d] = round(0.4 * cos + 0.6 * lex, 6)
        top_domains = sorted(dom_scores.items(), key=lambda x: -x[1])[:TOP_K_DOMAINS]
        res.domain_scores = dom_scores
        res.matched_domain = top_domains[0][0] if top_domains and top_domains[0][1] > 0 else None

        # ---- Level 2: tools inside candidate domains ----------------------
        cand = [i for i, d in enumerate(self._tool_domain) if d in dict(top_domains)]
        # always include standing tools
        for s in _STANDING_TOOLS:
            if s in self._tool_names:
                cand.append(self._tool_names.index(s))
        scores = {}
        if self._tool_vectors is not None:
            mat = self._tool_vectors[cand] @ qv if cand else np.zeros(0, dtype=np.float32)
            for j, i in enumerate(cand):
                cos = float(mat[j]) if j < len(mat) else 0.0
                lex = _dice(query, self._tool_lex[i])
                scores[self._tool_names[i]] = 0.4 * cos + 0.6 * lex
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        selected: List[Tool] = []
        seen = set()
        # standing tools first (they are the special RAG/search tools from the brief)
        for s in _STANDING_TOOLS:
            t = self.registry.get(s)
            if t is not None and s not in seen:
                selected.append(t)
                seen.add(s)
        for name, s in ranked:
            if len(selected) >= TOP_K_TOOLS + len(_STANDING_TOOLS):
                break
            if name in seen:
                continue
            t = self.registry.get(name)
            if t is not None:
                selected.append(t)
                seen.add(name)
        res.tools = selected
        res.tool_scores = {n: scores.get(n, 0.0) for n in [t.name for t in selected]}
        best_domain_tool = [v for k, v in res.tool_scores.items() if k not in _STANDING_TOOLS]
        res.confidence = max(best_domain_tool) if best_domain_tool else 0.0
        res.ms = (time.perf_counter() - start) * 1000
        return res
