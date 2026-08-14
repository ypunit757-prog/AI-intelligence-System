from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
