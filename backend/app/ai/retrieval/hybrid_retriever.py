
"""
Fuses vector similarity search and BM25 keyword search using
Reciprocal Rank Fusion (RRF) — combines two differently-scaled ranking
signals without needing to normalize raw scores against each other.
"""
from __future__ import annotations
from typing import Protocol, Sequence
from app.ai.retrieval.bm25_retriever import BM25Retriever, ScoredChunk


class VectorRetriever(Protocol):
    """Adapt this to whatever your existing vector search class exposes."""
    def search(self, query: str, top_k: int) -> list[ScoredChunk]: ...


def reciprocal_rank_fusion(
    ranked_lists: Sequence[list[ScoredChunk]], k: int = 60
) -> list[ScoredChunk]:
    """
    RRF score for a chunk = sum over each ranked list of 1 / (k + rank).
    k=60 is the standard default from the original RRF paper — it dampens
    the impact of any single list's top result dominating the fusion.
    """
    fused_scores: dict[str, float] = {}
    chunk_lookup: dict[str, ScoredChunk] = {}

    for ranked_list in ranked_lists:
        for rank, chunk in enumerate(ranked_list):
            fused_scores[chunk.chunk_id] = fused_scores.get(chunk.chunk_id, 0.0) + 1.0 / (k + rank + 1)
            chunk_lookup[chunk.chunk_id] = chunk

    ordered_ids = sorted(fused_scores, key=lambda cid: fused_scores[cid], reverse=True)
    return [
        ScoredChunk(
            chunk_id=cid,
            text=chunk_lookup[cid].text,
            score=fused_scores[cid],
            metadata=chunk_lookup[cid].metadata,
        )
        for cid in ordered_ids
    ]


class HybridRetriever:
    def __init__(self, vector_retriever: VectorRetriever, bm25_retriever: BM25Retriever):
        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever

    def search(self, query: str, top_k: int = 10, candidate_pool: int = 30) -> list[ScoredChunk]:
        # Pull a wider candidate pool from each source before fusing,
        # so RRF has enough overlap to actually re-rank meaningfully.
        vector_hits = self.vector_retriever.search(query, top_k=candidate_pool)
        keyword_hits = self.bm25_retriever.search(query, top_k=candidate_pool)
        fused = reciprocal_rank_fusion([vector_hits, keyword_hits])
        return fused[:top_k]