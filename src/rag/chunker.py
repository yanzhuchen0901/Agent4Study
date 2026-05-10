"""Recursive chapter-aware chunking."""

import re

from src.ingestion.models import TextbookSchema
from src.rag.models import Chunk


class RecursiveChunker:
    def __init__(self, target_size: int = 700, overlap: int = 80) -> None:
        self.target_size = target_size
        self.overlap = overlap

    def chunk_textbook(self, textbook: TextbookSchema) -> list[Chunk]:
        chunks: list[Chunk] = []
        for chapter in textbook.chapters:
            pieces = self._split(chapter.content)
            cursor = 0
            for piece in pieces:
                chunk_id = f"{textbook.textbook_id}_{chapter.chapter_id}_chunk_{len(chunks)+1:04d}"
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        textbook_id=textbook.textbook_id,
                        textbook_title=textbook.title,
                        chapter_id=chapter.chapter_id,
                        chapter=chapter.title,
                        page=chapter.page_start,
                        char_offset=cursor,
                        content=piece,
                        char_count=len(piece),
                    )
                )
                cursor += max(len(piece) - self.overlap, 0)
        return chunks

    def _split(self, text: str) -> list[str]:
        cleaned = re.sub(r"\n{3,}", "\n\n", text.strip())
        if not cleaned:
            return []
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", cleaned) if part.strip()]
        units = paragraphs or [cleaned]
        chunks: list[str] = []
        current = ""
        for unit in units:
            if len(unit) > self.target_size:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.extend(self._split_long(unit))
            elif len(current) + len(unit) + 2 <= self.target_size:
                current = f"{current}\n\n{unit}".strip()
            else:
                if current:
                    chunks.append(current)
                prefix = current[-self.overlap :] if current else ""
                current = f"{prefix}\n\n{unit}".strip()
        if current:
            chunks.append(current)
        return chunks

    def _split_long(self, text: str) -> list[str]:
        sentences = [s for s in re.split(r"(?<=[。！？.!?])", text) if s.strip()]
        if not sentences:
            sentences = [text[i : i + self.target_size] for i in range(0, len(text), self.target_size - self.overlap)]
        chunks: list[str] = []
        current = ""
        for sentence in sentences:
            if len(current) + len(sentence) <= self.target_size:
                current += sentence
            else:
                if current:
                    chunks.append(current.strip())
                prefix = current[-self.overlap :] if current else ""
                current = prefix + sentence
        if current:
            chunks.append(current.strip())
        return chunks
