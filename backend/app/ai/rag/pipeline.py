"""End-to-end RAG pipeline:

Query -> classify -> rewrite -> retrieve (hybrid) -> rerank
      -> compress -> prompt -> LLM -> citation verification -> answer
"""
from dataclasses import dataclass, field
from typing import AsyncIterator, List

from app.ai.retrieval.factory import get_embedding_model
from app.ai.llm.factory import get_llm
from app.ai.llm.interface import ChatMessage
from app.ai.prompts.rag_prompts import SYSTEM_PROMPT, build_user_prompt
from app.ai.reranking.reranker import rerank
from app.ai.retrieval.factory import get_vector_store
from app.config.settings import get_settings


@dataclass
class RagResult:
    answer: str
    sources: List[dict] = field(default_factory=list)


def _classify_query(query: str) -> str:
    """Very small heuristic classifier — placeholder for a future
    fine-tuned or LLM-based classifier. Distinguishes conversational
    chit-chat from knowledge-seeking queries so short-circuiting is
    possible later without changing the pipeline's public shape."""
    trivial_markers = {"hi", "hello", "hey", "thanks", "thank you"}
    return "chitchat" if query.strip().lower() in trivial_markers else "knowledge"


def _rewrite_query(query: str) -> str:
    """Placeholder for query rewriting/expansion. Kept as a pure
    function so an LLM-based rewrite can be swapped in without
    touching pipeline control flow."""
    return query.strip()


def _compress_context(chunks: List[dict], max_chunks: int) -> List[dict]:
    return chunks[:max_chunks]


def _verify_citations(answer: str, chunk_count: int) -> str:
    """Confirms cited indices like [1], [2] actually exist in context;
    strips citations that reference out-of-range indices to avoid
    fabricated sourcing."""
    import re

    def _replace(match: "re.Match") -> str:
        idx = int(match.group(1))
        return match.group(0) if 1 <= idx <= chunk_count else ""

    return re.sub(r"\[(\d+)\]", _replace, answer)


async def run_rag(query: str, user_id: str) -> RagResult:
    settings = get_settings()
    classification = _classify_query(query)
    if classification == "chitchat":
        return RagResult(answer="Hi! Ask me anything about your uploaded documents.", sources=[])

    rewritten = _rewrite_query(query)

    embedder = get_embedding_model()
    query_embedding = embedder.embed_query(rewritten)

    store = get_vector_store()
    retrieved = await store.similarity_search(query_embedding, top_k=settings.top_k * 2, user_id=user_id)
    retrieved = [r for r in retrieved if r["score"] >= settings.similarity_threshold]

    reranked = rerank(rewritten, list(retrieved))
    context_chunks = _compress_context(reranked, max_chunks=settings.top_k)

    if not context_chunks:
        return RagResult(
            answer="I couldn't find anything relevant in your documents to answer that.",
            sources=[],
        )

    user_prompt = build_user_prompt(rewritten, context_chunks)
    messages: List[ChatMessage] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    llm = get_llm()
    raw_answer = await llm.generate(messages)
    verified_answer = _verify_citations(raw_answer, len(context_chunks))

    sources = [
        {"chunk_id": c["chunk_id"], "document_id": c["document_id"], "score": c["score"], "excerpt": c["content"][:280]}
        for c in context_chunks
    ]
    return RagResult(answer=verified_answer, sources=sources)


async def stream_rag(query: str, user_id: str) -> AsyncIterator[str]:
    """Streaming variant used by the /chat SSE endpoint. Retrieval is
    identical to run_rag; only generation is streamed."""
    settings = get_settings()
    rewritten = _rewrite_query(query)
    embedder = get_embedding_model()
    query_embedding = embedder.embed_query(rewritten)

    store = get_vector_store()
    retrieved = await store.similarity_search(query_embedding, top_k=settings.top_k * 2, user_id=user_id)
    retrieved = [r for r in retrieved if r["score"] >= settings.similarity_threshold]
    reranked = rerank(rewritten, list(retrieved))
    context_chunks = _compress_context(reranked, max_chunks=settings.top_k)

    if not context_chunks:
        yield "I couldn't find anything relevant in your documents to answer that."
        return

    user_prompt = build_user_prompt(rewritten, context_chunks)
    messages: List[ChatMessage] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    llm = get_llm()
    async for delta in llm.stream(messages):
        yield delta
