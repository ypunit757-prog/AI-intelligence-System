from functools import lru_cache

from app.ai.retrieval.faiss_store import FaissVectorStore
from app.ai.retrieval.pgvector_store import PgVectorStore
from app.ai.retrieval.vector_store_interface import VectorStoreInterface
from app.config.settings import get_settings


def get_embedding_model():
    """Import the embedding provider lazily, based on settings, so the
    heavy sentence-transformers/torch stack is never imported unless
    EMBEDDING_PROVIDER=local is explicitly configured."""
    settings = get_settings()
    if settings.embedding_provider == "local":
        from app.ai.embeddings.sentence_transformer_embeddings import get_embedding_model as _get_local

        return _get_local()

    from app.ai.embeddings.gemini_embeddings import get_gemini_embedding_model

    return get_gemini_embedding_model()


@lru_cache
def get_vector_store() -> VectorStoreInterface:
    settings = get_settings()
    if settings.vector_store == "pgvector":
        from app.database.session import AsyncSessionLocal

        return PgVectorStore(AsyncSessionLocal)

    dim = get_embedding_model().dimension
    return FaissVectorStore(index_dir=settings.faiss_index_dir, dimension=dim)