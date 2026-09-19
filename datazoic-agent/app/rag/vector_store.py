"""Hybrid (vector + BM25) retrieval over a SQLite-persisted vector store.

Design notes
------------
* Vectors are stored as float32 blobs in SQLite — zero external services.
  For 600-20k documents this loads into memory in milliseconds; for
  millions you would graduate to FAISS/pgvector/Qdrant behind the same
  `search()` interface (see DESIGN.md, Scalability).
* BM25 is computed in pure Python over the cached token lists, giving
  strong keyword recall for identifiers (error codes, endpoint paths,
  policy names) that embedding models dilute.
* `hybrid_search` blends normalized cosine similarity with normalized
  BM25 scores (configurable weight) and supports section filtering, so a
  single store serves all five knowledge-base sections.
"""
from __future__ import annotations

import json
import math
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from .embedder import HashingEmbedder, tokenize


@dataclass
class Document:
    id: str
    section: str
    title: str
    content: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class Hit:
    id: str
    section: str
    title: str
    content: str
    score: float
    vector_score: float
    bm25_score: float
    metadata: Dict

    def snippet(self, chars: int = 300) -> str:
        c = " ".join(self.content.split())
        return c[:chars].rstrip()


class _Index:
    """In-memory search index rebuilt lazily after writes."""

    def __init__(self, ids, sections, titles, contents, metadata, vectors, doc_tokens):
        self.ids = ids
        self.sections = sections
        self.titles = titles
        self.contents = contents
        self.metadata = metadata
        self.vectors = vectors  # np.ndarray (n, dim), unit norm
        self.doc_tokens = doc_tokens
        self.doc_len = np.array([len(t) for t in doc_tokens], dtype=np.float32)
        self.n = len(ids)
        self.avgdl = float(self.doc_len.mean()) if self.n else 0.0
        # document frequency per term
        df: Dict[str, int] = {}
        for toks in doc_tokens:
            for t in set(toks):
                df[t] = df.get(t, 0) + 1
        self.df = df
        self.term_postings: Dict[str, Dict[int, int]] = {}
        for i, toks in enumerate(doc_tokens):
            for t in toks:
                self.term_postings.setdefault(t, {}).setdefault(i, 0)
                self.term_postings[t][i] += 1
        self.idf = {
            t: math.log((self.n - d + 0.5) / (d + 0.5) + 1.0) for t, d in df.items()
        }

    def bm25_scores(self, query_tokens: List[str], k1: float = 1.5, b: float = 0.75) -> np.ndarray:
        scores = np.zeros(self.n, dtype=np.float32)
        for qt in query_tokens:
            postings = self.term_postings.get(qt)
            idf = self.idf.get(qt, 0.0)
            if not postings or idf <= 0:
                continue
            for i, tf in postings.items():
                denom = tf + k1 * (1.0 - b + b * self.doc_len[i] / (self.avgdl or 1.0))
                scores[i] += idf * (tf * (k1 + 1.0)) / denom
        return scores

    def normalize(self, x: np.ndarray) -> np.ndarray:
        m = float(x.max())
        return x / m if m > 0 else x


class VectorStore:
    def __init__(self, path: str | Path, dim: int = 256):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.dim = dim
        self.embedder = HashingEmbedder(dim)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self._lock = threading.RLock()
        self._index: Optional[_Index] = None
        self._init_schema()

    # -- schema ----------------------------------------------------------
    def _init_schema(self) -> None:
        with self._lock:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    section TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    embedding BLOB NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_documents_section ON documents(section);
                CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
                """
            )
            self.conn.commit()

    # -- writes ------------------------------------------------------------
    def replace_all(self, docs: List[Document]) -> int:
        with self._lock:
            vecs = self.embedder.embed_batch([f"{d.title}\n{d.content}" for d in docs])
            now = time.time()
            self.conn.execute("DELETE FROM documents")
            self.conn.executemany(
                "INSERT INTO documents (id, section, title, content, metadata, embedding, updated_at)"
                " VALUES (?,?,?,?,?,?,?)",
                [
                    (d.id, d.section, d.title, d.content, json.dumps(d.metadata),
                     vecs[i].astype(np.float32).tobytes(), now)
                    for i, d in enumerate(docs)
                ],
            )
            self.conn.commit()
            self._index = None
            return len(docs)

    def add(self, docs: List[Document]) -> int:
        with self._lock:
            now = time.time()
            for d in docs:
                v = self.embedder.embed(f"{d.title}\n{d.content}").astype(np.float32).tobytes()
                self.conn.execute(
                    "INSERT OR REPLACE INTO documents (id, section, title, content, metadata, embedding, updated_at)"
                    " VALUES (?,?,?,?,?,?,?)",
                    (d.id, d.section, d.title, d.content, json.dumps(d.metadata), v, now),
                )
            self.conn.commit()
            self._index = None
            return len(docs)

    # -- index -------------------------------------------------------------
    def _load_index(self) -> _Index:
        if self._index is not None:
            return self._index
        with self._lock:
            if self._index is not None:
                return self._index
            rows = self.conn.execute(
                "SELECT id, section, title, content, metadata, embedding FROM documents"
            ).fetchall()
            ids = [r[0] for r in rows]
            sections = [r[1] for r in rows]
            titles = [r[2] for r in rows]
            contents = [r[3] for r in rows]
            metadata = [json.loads(r[4]) for r in rows]
            vectors = np.stack(
                [np.frombuffer(r[5], dtype=np.float32) for r in rows]
            ) if rows else np.zeros((0, self.dim), dtype=np.float32)
            doc_tokens = [tokenize(f"{t}\n{c}") for t, c in zip(titles, contents)]
            self._index = _Index(ids, sections, titles, contents, metadata, vectors, doc_tokens)
            return self._index

    # -- reads ---------------------------------------------------------------
    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        vector_weight: float = 0.65,
        section: Optional[str] = None,
    ) -> List[Hit]:
        idx = self._load_index()
        if idx.n == 0:
            return []
        mask = np.ones(idx.n, dtype=bool)
        if section:
            mask = np.array([s == section for s in idx.sections])
        qv = self.embedder.embed(query)
        cos = idx.vectors @ qv if idx.n else np.zeros(0, dtype=np.float32)
        bm = idx.bm25_scores(tokenize(query))
        cos_n, bm_n = idx.normalize(cos), idx.normalize(bm)
        score = vector_weight * cos_n + (1.0 - vector_weight) * bm_n
        score = np.where(mask, score, -np.inf)
        order = np.argsort(score)[::-1][:top_k]
        hits = []
        for i in order:
            if score[i] <= -1e9:
                continue
            hits.append(
                Hit(
                    id=idx.ids[i],
                    section=idx.sections[i],
                    title=idx.titles[i],
                    content=idx.contents[i],
                    score=float(score[i]),
                    vector_score=float(cos_n[i]),
                    bm25_score=float(bm_n[i]),
                    metadata=idx.metadata[i],
                )
            )
        return hits

    def sections(self) -> Dict[str, int]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT section, COUNT(*) FROM documents GROUP BY section ORDER BY section"
            ).fetchall()
        return {s: c for s, c in rows}

    def count(self) -> int:
        with self._lock:
            return int(self.conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0])
