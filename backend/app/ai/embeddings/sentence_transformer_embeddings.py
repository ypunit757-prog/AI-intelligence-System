"""Sentence-Transformers embedding provider with automatic device detection.

The model is loaded once per process (module-level cache) — never
re-initialize it per request.
"""
from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

from app.ai.embeddings.interface import EmbeddingInterface


def _detect_device() -> str:
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


class SentenceTransformerEmbeddings(EmbeddingInterface):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.device = _detect_device()
        self._model = SentenceTransformer(model_name, device=self.device)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        vectors = self._model.encode(texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
        return vectors.tolist()

    def embed_query(self, text: str) -> List[float]:
        vector = self._model.encode([text], normalize_embeddings=True)[0]
        return vector.tolist()

    @property
    def dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()


@lru_cache
def get_embedding_model() -> "SentenceTransformerEmbeddings":
    from app.config.settings import get_settings

    settings = get_settings()
    return SentenceTransformerEmbeddings(settings.embedding_model)
