"""FAISS-backed vector store for local development.

Keeps a flat index in memory, persisted to disk as (index.faiss +
metadata.json) so it survives process restarts locally. Not intended
for production — use pgvector there.
"""
import json
import os
import threading
from pathlib import Path
from typing import List

import faiss
import numpy as np

from app.ai.retrieval.vector_store_interface import RetrievedChunk, VectorStoreInterface


class FaissVectorStore(VectorStoreInterface):
    def __init__(self, index_dir: str, dimension: int):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.dimension = dimension
        self._lock = threading.Lock()
        self._index_path = self.index_dir / "index.faiss"
        self._meta_path = self.index_dir / "metadata.json"
        self._metadata: list[dict] = []
        self._load()

    def _load(self) -> None:
        if self._index_path.exists() and self._meta_path.exists():
            self._index = faiss.read_index(str(self._index_path))
            with open(self._meta_path) as f:
                self._metadata = json.load(f)
        else:
            self._index = faiss.IndexFlatIP(self.dimension)
            self._metadata = []

    def _persist(self) -> None:
        faiss.write_index(self._index, str(self._index_path))
        with open(self._meta_path, "w") as f:
            json.dump(self._metadata, f)

    async def add(self, chunk_id: str, document_id: str, content: str, embedding: List[float], metadata: dict) -> None:
        with self._lock:
            vec = np.array([embedding], dtype="float32")
            self._index.add(vec)
            self._metadata.append(
                {"chunk_id": chunk_id, "document_id": document_id, "content": content, "metadata": metadata}
            )
            self._persist()

    async def delete_by_document(self, document_id: str) -> None:
        # FAISS flat index has no efficient delete-by-id; rebuild instead.
        with self._lock:
            keep = [(i, m) for i, m in enumerate(self._metadata) if m["document_id"] != document_id]
            if len(keep) == len(self._metadata):
                return
            new_index = faiss.IndexFlatIP(self.dimension)
            if keep:
                vectors = np.vstack([self._index.reconstruct(i) for i, _ in keep])
                new_index.add(vectors)
            self._index = new_index
            self._metadata = [m for _, m in keep]
            self._persist()

    async def similarity_search(self, query_embedding: List[float], top_k: int, user_id: str | None = None) -> List[RetrievedChunk]:
        with self._lock:
            if self._index.ntotal == 0:
                return []
            vec = np.array([query_embedding], dtype="float32")
            k = min(top_k, self._index.ntotal)
            scores, indices = self._index.search(vec, k)
            results: List[RetrievedChunk] = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:
                    continue
                m = self._metadata[idx]
                results.append(
                    RetrievedChunk(
                        chunk_id=m["chunk_id"],
                        document_id=m["document_id"],
                        content=m["content"],
                        metadata=m["metadata"],
                        score=float(score),
                    )
                )
            return results
