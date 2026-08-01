"""Lightweight local embeddings for memory semantic search (no heavy deps)."""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Sequence


EMBED_DIM = 256


def embed_text(text: str, dim: int = EMBED_DIM) -> List[float]:
    """Hashing bag-of-words embedding with L2 normalization."""
    vec = [0.0] * dim
    tokens = [t for t in text.lower().split() if t]
    if not tokens:
        return vec
    for token in tokens:
        h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        vec[h % dim] += 1.0
        # bigram boost
        if len(token) > 2:
            h2 = int(hashlib.sha1(token[:3].encode("utf-8")).hexdigest(), 16)
            vec[h2 % dim] += 0.5
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return float(sum(x * y for x, y in zip(a, b)))


class VectorIndex:
    """SQLite-backed vector index under workspace/memory/."""

    def __init__(self, storage_path: Path):
        self.db_path = Path(storage_path) / "vectors.sqlite"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS vectors ("
            "memory_id TEXT PRIMARY KEY, "
            "embedding TEXT NOT NULL)"
        )
        self._conn.commit()

    def upsert(self, memory_id: str, text: str) -> None:
        emb = embed_text(text)
        self._conn.execute(
            "INSERT OR REPLACE INTO vectors(memory_id, embedding) VALUES (?, ?)",
            (memory_id, json.dumps(emb)),
        )
        self._conn.commit()

    def delete(self, memory_id: str) -> None:
        self._conn.execute("DELETE FROM vectors WHERE memory_id = ?", (memory_id,))
        self._conn.commit()

    def get(self, memory_id: str) -> Optional[List[float]]:
        row = self._conn.execute(
            "SELECT embedding FROM vectors WHERE memory_id = ?", (memory_id,)
        ).fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def search(
        self, query: str, memory_ids: Optional[List[str]] = None, top_k: int = 10
    ) -> List[tuple[str, float]]:
        q = embed_text(query)
        if memory_ids is not None and not memory_ids:
            return []
        if memory_ids is None:
            rows = self._conn.execute("SELECT memory_id, embedding FROM vectors").fetchall()
        else:
            placeholders = ",".join("?" * len(memory_ids))
            rows = self._conn.execute(
                f"SELECT memory_id, embedding FROM vectors WHERE memory_id IN ({placeholders})",
                memory_ids,
            ).fetchall()
        scored: List[tuple[str, float]] = []
        for mid, emb_json in rows:
            score = cosine_similarity(q, json.loads(emb_json))
            if score > 0.05:
                scored.append((mid, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def close(self) -> None:
        self._conn.close()
