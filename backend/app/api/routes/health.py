from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.retrieval.factory import get_vector_store
from app.database.session import get_db

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    return {"name": "AI Knowledge Intelligence Platform", "status": "ok"}


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)):
    checks = {"database": "unknown", "vector_store": "unknown"}

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    try:
        get_vector_store()
        checks["vector_store"] = "ok"
    except Exception as e:
        checks["vector_store"] = f"error: {e}"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
