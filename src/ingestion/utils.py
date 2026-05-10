"""Utilities shared by ingestion parsers."""

from pathlib import Path
import re

from src.ingestion.models import ChapterSchema, TextbookSchema


CHAPTER_PATTERN = re.compile(
    r"^\s*(第\s*[一二三四五六七八九十百千万\d]+\s*[章节篇]|#{1,3}\s+|Chapter\s+\d+)",
    re.IGNORECASE,
)


def make_textbook_id(path: Path) -> str:
    stem = re.sub(r"[^0-9a-zA-Z_\-\u4e00-\u9fff]+", "_", path.stem).strip("_")
    return stem or "book_01"


def normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    compact: list[str] = []
    blank = False
    for line in lines:
        if not line:
            if not blank:
                compact.append("")
            blank = True
            continue
        compact.append(line)
        blank = False
    return "\n".join(compact).strip()


def make_chapter(index: int, title: str, content: str, page_start: int = 1, page_end: int = 1) -> ChapterSchema:
    cleaned = normalize_text(content)
    return ChapterSchema(
        chapter_id=f"ch_{index:02d}",
        title=title.strip() or f"第 {index} 章",
        page_start=page_start,
        page_end=max(page_end, page_start),
        content=cleaned,
        char_count=len(cleaned),
    )


def split_text_into_chapters(text: str, default_title: str, page_start: int = 1, page_end: int = 1) -> list[ChapterSchema]:
    normalized = normalize_text(text)
    if not normalized:
        return [make_chapter(1, default_title, "", page_start, page_end)]

    sections: list[tuple[str, list[str]]] = []
    current_title = default_title
    current_lines: list[str] = []

    for line in normalized.splitlines():
        is_heading = bool(CHAPTER_PATTERN.match(line)) and len(line) <= 80
        if is_heading and current_lines:
            sections.append((current_title, current_lines))
            current_title = line.lstrip("#").strip()
            current_lines = [line]
        elif is_heading:
            current_title = line.lstrip("#").strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, current_lines))

    if not sections:
        sections = [(default_title, [normalized])]

    return [
        make_chapter(i, title, "\n".join(lines), page_start, page_end)
        for i, (title, lines) in enumerate(sections, 1)
    ]


def build_textbook(path: Path, textbook_id: str | None, title: str, total_pages: int, chapters: list[ChapterSchema]) -> TextbookSchema:
    return TextbookSchema(
        textbook_id=textbook_id or make_textbook_id(path),
        filename=path.name,
        title=title or path.stem,
        total_pages=total_pages,
        total_chars=sum(chapter.char_count for chapter in chapters),
        chapters=chapters,
    )
