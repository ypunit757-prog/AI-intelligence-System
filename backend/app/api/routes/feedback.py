from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Feedback, User
from app.database.session import get_db
from app.schemas.feedback import FeedbackRequest
from app.security.auth import get_current_user

router = APIRouter(tags=["feedback"])


@router.post("/feedback", status_code=201)
async def submit_feedback(payload: FeedbackRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    fb = Feedback(
        user_id=user.id,
        message_id=payload.message_id,
        question=payload.question,
        answer=payload.answer,
        sources=payload.sources,
        rating=payload.rating,
    )
    db.add(fb)
    await db.commit()
    return {"status": "recorded"}


@router.get("/metrics")
async def metrics():
    # Minimal placeholder metrics endpoint; wire to Prometheus/OpenTelemetry
    # in a later iteration if deeper observability is needed.
    return {"status": "ok", "note": "Extend with real counters/histograms as needed."}
