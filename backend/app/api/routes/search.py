import time

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.retrieval.factory import get_embedding_model
from app.ai.retrieval.factory import get_vector_store
from app.database.models import SearchLog, User
from app.database.session import get_db
from app.schemas.search import SearchRequest, SearchResponse, SearchResultItem
from app.security.auth import get_current_user

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(payload: SearchRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    start = time.monotonic()
    embedder = get_embedding_model()
    query_embedding = embedder.embed_query(payload.query)

    store = get_vector_store()
    results = await store.similarity_search(query_embedding, top_k=payload.top_k, user_id=user.id)

    latency_ms = int((time.monotonic() - start) * 1000)
    db.add(SearchLog(user_id=user.id, query=payload.query, top_k=payload.top_k, latency_ms=latency_ms))
    await db.commit()

    return SearchResponse(results=[SearchResultItem(**r) for r in results])
