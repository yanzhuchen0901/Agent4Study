"""Textbook ingestion package."""

from abc import ABC, abstractmethod
from pathlib import Path

from src.ingestion.models import TextbookSchema


class BaseParser(ABC):
    """Common interface for textbook parsers."""

    @abstractmethod
    def parse(self, file_path: Path, textbook_id: str | None = None) -> TextbookSchema:
        """Parse a source file into the shared textbook schema."""
