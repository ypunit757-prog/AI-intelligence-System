from abc import ABC, abstractmethod
from typing import List, TypedDict


class RetrievedChunk(TypedDict):
    chunk_id: str
    document_id: str
    content: str
    metadata: dict
    score: float


class VectorStoreInterface(ABC):
    @abstractmethod
    async def add(self, chunk_id: str, document_id: str, content: str, embedding: List[float], metadata: dict) -> None:
        ...

    @abstractmethod
    async def delete_by_document(self, document_id: str) -> None:
        ...

    @abstractmethod
    async def similarity_search(self, query_embedding: List[float], top_k: int, user_id: str | None = None) -> List[RetrievedChunk]:
        ...
