from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    message_id: str | None = None
    question: str
    answer: str
    sources: list[dict] = []
    rating: int = Field(..., ge=-1, le=1)
