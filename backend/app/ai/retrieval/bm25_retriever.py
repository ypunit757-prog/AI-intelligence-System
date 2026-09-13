
"""
Keyword-based retrieval using BM25, to be fused with vector search results.
Requires: pip install rank-bm25
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Sequence
from rank_bm25 import BM25Okapi


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


@dataclass
class ScoredChunk:
    chunk_id: str
    text: str
    score: float
    metadata: dict


class BM25Retriever:
    """
    In-memory BM25 index over a document's chunks.
    Build one per-document (or per-corpus, if your dataset is small enough
    to keep resident) and reuse it across queries.
    """

    def __init__(self, chunks: Sequence[dict]):
        # each chunk: {"id": str, "text": str, "metadata": dict}
        self._chunks = list(chunks)
        self._corpus_tokens = [_tokenize(c["text"]) for c in self._chunks]
        self._bm25 = BM25Okapi(self._corpus_tokens)

    def search(self, query: str, top_k: int = 10) -> list[ScoredChunk]:
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(
            zip(self._chunks, scores), key=lambda x: x[1], reverse=True
        )[:top_k]
        return [
            ScoredChunk(
                chunk_id=c["id"], text=c["text"], score=float(s), metadata=c.get("metadata", {})
            )
            for c, s in ranked
            if s > 0
        ]