"""Excel textbook parser."""

from pathlib import Path

import pandas as pd

from src.ingestion import BaseParser
from src.ingestion.models import TextbookSchema
from src.ingestion.utils import build_textbook, make_chapter


class ExcelParser(BaseParser):
    def parse(self, file_path: Path, textbook_id: str | None = None) -> TextbookSchema:
        sheets = pd.read_excel(file_path, sheet_name=None, header=None)
        chapters = []
        for index, (sheet_name, frame) in enumerate(sheets.items(), 1):
            rows = []
            for row in frame.fillna("").astype(str).values.tolist():
                line = " | ".join(cell.strip() for cell in row if cell.strip())
                if line:
                    rows.append(line)
            chapters.append(make_chapter(index, sheet_name, "\n".join(rows)))
        if not chapters:
            chapters = [make_chapter(1, file_path.stem, "")]
        return build_textbook(file_path, textbook_id, file_path.stem, len(chapters), chapters)
