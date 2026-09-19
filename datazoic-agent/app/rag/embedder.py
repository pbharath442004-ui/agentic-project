"""Offline, deterministic embeddings.

`HashingEmbedder` implements signed feature hashing (the same trick used by
liblinear / sklearn's FeatureHasher):

* tokenize (lowercase alphanumerics)
* hash each token to a bucket index (md5) and a sign bit
* accumulate, L2-normalize

This gives 256-dim unit vectors with no model download and no network access.
Combined with BM25 (see `vector_store.py`) the hybrid retriever performs well
for keyword-dense domain content such as API docs, policies and guides —
which is exactly what the prototype's knowledge base contains.

The `Embedder` interface means you can swap in `sentence-transformers`
(e.g. `all-MiniLM-L6-v2`) in production without touching retrieval code.
"""
from __future__ import annotations

import hashlib
import re
from typing import Iterable, List

import numpy as np

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> List[str]:
    """Lowercase alphanumeric tokenization (shared by embedder + BM25)."""
    return _TOKEN_RE.findall(text.lower())


class HashingEmbedder:
    name = "hashing-256"

    def __init__(self, dim: int = 256):
        self.dim = dim

    def embed(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        if text:
            for tok in tokenize(text):
                h = int(hashlib.md5(tok.encode("utf-8")).hexdigest()[:12], 16)
                idx = h % self.dim
                sign = 1.0 if (h >> 16) & 1 else -1.0
                v[idx] += sign
        n = float(np.linalg.norm(v))
        if n > 0:
            v /= n
        return v

    def embed_batch(self, texts: Iterable[str]) -> np.ndarray:
        return np.stack([self.embed(t) for t in texts]) if list(texts) else np.zeros((0, self.dim), dtype=np.float32)

    @staticmethod
    def cosine(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b))  # inputs are unit-norm
