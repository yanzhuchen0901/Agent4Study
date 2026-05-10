"""DOCX textbook parser."""

from pathlib import Path

from docx import Document

from src.ingestion import BaseParser
from src.ingestion.models import TextbookSchema
from src.ingestion.utils import build_textbook, make_chapter


class DOCXParser(BaseParser):
    def parse(self, file_path: Path, textbook_id: str | None = None) -> TextbookSchema:
        document = Document(str(file_path))
        sections: list[tuple[str, list[str]]] = []
        current_title = file_path.stem
        current_lines: list[str] = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
            style_name = paragraph.style.name.lower() if paragraph.style else ""
            if style_name.startswith("heading") and current_lines:
                sections.append((current_title, current_lines))
                current_title = text
                current_lines = [text]
            elif style_name.startswith("heading"):
                current_title = text
                current_lines = [text]
            else:
                current_lines.append(text)

        if current_lines:
            sections.append((current_title, current_lines))
        if not sections:
            sections = [(file_path.stem, [])]

        chapters = [
            make_chapter(i, title, "\n".join(lines))
            for i, (title, lines) in enumerate(sections, 1)
        ]
        return build_textbook(file_path, textbook_id, file_path.stem, len(chapters), chapters)
