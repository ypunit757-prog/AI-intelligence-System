"""Optional cross-encoder reranker.

If RERANKER_MODEL is unset, reranking is skipped and hybrid-search
scores are used as-is (keeps the app fully functional with zero extra
model downloads by default).
"""
from functools import lru_cache
from typing import List

from app.config.settings import get_settings


@lru_cache
def _get_cross_encoder():
    settings = get_settings()
    if not settings.reranker_model:
        return None
    from sentence_transformers import CrossEncoder

    return CrossEncoder(settings.reranker_model)


def rerank(query: str, chunks: List[dict]) -> List[dict]:
    model = _get_cross_encoder()
    if model is None or not chunks:
        return chunks

    pairs = [(query, c["content"]) for c in chunks]
    scores = model.predict(pairs)
    for c, s in zip(chunks, scores):
        c["rerank_score"] = float(s)
    return sorted(chunks, key=lambda c: c["rerank_score"], reverse=True)
