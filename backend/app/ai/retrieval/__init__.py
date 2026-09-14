# wherever retrieval is currently called, e.g. app/ai/retrieval/__init__.py
from app.config.settings import settings
from app.ai.retrieval.hybrid_retriever import HybridRetriever
from app.ai.retrieval.bm25_retriever import BM25Retriever

def get_retriever(vector_retriever, document_chunks):
    if settings.RETRIEVAL_MODE == "hybrid":
        bm25 = BM25Retriever(document_chunks)
        return HybridRetriever(vector_retriever, bm25)
    return vector_retriever