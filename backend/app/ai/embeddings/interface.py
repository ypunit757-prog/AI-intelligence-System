from abc import ABC, abstractmethod
from typing import List


class EmbeddingInterface(ABC):
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of documents/chunks."""

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query string."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        ...
