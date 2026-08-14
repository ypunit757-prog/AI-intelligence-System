from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    mime_type: str
    size: int
    created_at: datetime

    class Config:
        from_attributes = True
