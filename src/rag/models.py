"""RAG data models."""

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    chunk_id: str
    textbook_id: str
    textbook_title: str
    chapter_id: str
    chapter: str
    page: int
    char_offset: int
    content: str
    char_count: int = Field(ge=0)


class Citation(BaseModel):
    textbook: str
    chapter: str
    page: int
    relevance_score: float = Field(ge=0.0, le=1.0)
    chunk_id: str


class RAGIndexResult(BaseModel):
    status: str
    textbook_id: str
    chunks: int
    dimension: int


class RAGStatus(BaseModel):
    indexed: bool
    chunks: int
    dimension: int
    textbook_ids: list[str]


class RAGQueryResult(BaseModel):
    answer: str
    citations: list[Citation]
    source_chunks: list[str]
