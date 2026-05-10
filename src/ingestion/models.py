"""Shared ingestion data models."""

from pydantic import BaseModel, Field


class ChapterSchema(BaseModel):
    chapter_id: str
    title: str
    page_start: int = 1
    page_end: int = 1
    content: str
    char_count: int = Field(ge=0)


class TextbookSchema(BaseModel):
    textbook_id: str
    filename: str
    title: str
    total_pages: int = Field(ge=0)
    total_chars: int = Field(ge=0)
    chapters: list[ChapterSchema]


class TextbookSummary(BaseModel):
    textbook_id: str
    filename: str
    title: str
    total_pages: int
    total_chars: int
    chapter_count: int
