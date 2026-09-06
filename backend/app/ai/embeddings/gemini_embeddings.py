"""Gemini API-based embedding provider.

Uses Google's embedContent/batchEmbedContents REST endpoints over plain
HTTP (via httpx, already a dependency) instead of a locally-loaded
model. This avoids importing sentence-transformers/torch entirely,
which is the single biggest RAM cost in this app (commonly 500MB+ just
to import) — critical for fitting inside a 512MB Render instance.
"""
from functools import lru_cache
from typing import List

import httpx

from app.ai.embeddings.interface import EmbeddingInterface

_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# text-embedding-004's native output dimension. Overridable via the
# GEMINI_EMBEDDING_DIMENSION setting if a different Gemini embedding
# model is ever configured.
_DEFAULT_DIMENSION = 768


class GeminiEmbeddings(EmbeddingInterface):
    def __init__(self, api_key: str, model_name: str, dimension: int = _DEFAULT_DIMENSION):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required when EMBEDDING_PROVIDER=gemini")
        self.api_key = api_key
        # Gemini model names are addressed as "models/<name>".
        self.model_name = model_name if model_name.startswith("models/") else f"models/{model_name}"
        self._dimension = dimension
        self._client = httpx.Client(timeout=30.0)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        url = f"{_API_BASE}/{self.model_name}:batchEmbedContents"
        body = {
            "requests": [
                {"model": self.model_name, "content": {"parts": [{"text": t}]}} for t in texts
            ]
        }
        resp = self._client.post(url, params={"key": self.api_key}, json=body)
        resp.raise_for_status()
        data = resp.json()
        return [item["values"] for item in data["embeddings"]]

    def embed_query(self, text: str) -> List[float]:
        url = f"{_API_BASE}/{self.model_name}:embedContent"
        body = {"model": self.model_name, "content": {"parts": [{"text": text}]}}
        resp = self._client.post(url, params={"key": self.api_key}, json=body)
        resp.raise_for_status()
        return resp.json()["embedding"]["values"]

    @property
    def dimension(self) -> int:
        return self._dimension


@lru_cache
def get_gemini_embedding_model() -> "GeminiEmbeddings":
    from app.config.settings import get_settings

    settings = get_settings()
    return GeminiEmbeddings(
        api_key=settings.gemini_api_key,
        model_name=settings.embedding_model,
        dimension=settings.embedding_dimension,
    )