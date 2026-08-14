"""pgvector-backed vector store for production.

Stores embeddings directly on document_chunks so a single SQL query
does hybrid retrieval (vector distance + optional metadata filters)
without a network hop to a separate vector service.
"""
from typing import List

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Document, DocumentChunk
from app.ai.retrieval.vector_store_interface import RetrievedChunk, VectorStoreInterface


class PgVectorStore(VectorStoreInterface):
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def add(self, chunk_id: str, document_id: str, content: str, embedding: List[float], metadata: dict) -> None:
        async with self._session_factory() as session:  # type: AsyncSession
            chunk = DocumentChunk(
                id=chunk_id,
                document_id=document_id,
                content=content,
                embedding=embedding,
                chunk_metadata=metadata,
                chunk_index=metadata.get("chunk_index", 0),
            )
            session.add(chunk)
            await session.commit()

    async def delete_by_document(self, document_id: str) -> None:
        async with self._session_factory() as session:
            await session.execute(text("DELETE FROM document_chunks WHERE document_id = :doc_id"), {"doc_id": document_id})
            await session.commit()

    async def similarity_search(self, query_embedding: List[float], top_k: int, user_id: str | None = None) -> List[RetrievedChunk]:
        async with self._session_factory() as session:
            # Cosine distance via pgvector's <=> operator; join to enforce
            # per-user isolation when user_id is provided.
            query = (
                select(
                    DocumentChunk.id,
                    DocumentChunk.document_id,
                    DocumentChunk.content,
                    DocumentChunk.chunk_metadata,
                    DocumentChunk.embedding.cosine_distance(query_embedding).label("distance"),
                )
                .join(Document, Document.id == DocumentChunk.document_id)
                .order_by("distance")
                .limit(top_k)
            )
            if user_id:
                query = query.where(Document.user_id == user_id)

            rows = (await session.execute(query)).all()
            return [
                RetrievedChunk(
                    chunk_id=row.id,
                    document_id=row.document_id,
                    content=row.content,
                    metadata=row.chunk_metadata or {},
                    score=1.0 - float(row.distance),
                )
                for row in rows
            ]
