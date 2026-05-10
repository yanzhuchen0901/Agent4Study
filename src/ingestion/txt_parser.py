"""Plain text textbook parser."""

from pathlib import Path

from src.ingestion import BaseParser
from src.ingestion.models import TextbookSchema
from src.ingestion.utils import build_textbook, split_text_into_chapters


class TXTParser(BaseParser):
    def parse(self, file_path: Path, textbook_id: str | None = None) -> TextbookSchema:
        text = file_path.read_text(encoding="utf-8-sig", errors="ignore")
        chapters = split_text_into_chapters(text, file_path.stem)
        return build_textbook(file_path, textbook_id, file_path.stem, len(chapters), chapters)
