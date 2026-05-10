"""Parser dispatch for supported textbook formats."""

from pathlib import Path

from src.ingestion import BaseParser
from src.ingestion.docx_parser import DOCXParser
from src.ingestion.excel_parser import ExcelParser
from src.ingestion.md_parser import MarkdownParser
from src.ingestion.pdf_parser import PDFParser
from src.ingestion.txt_parser import TXTParser


class ParserFactory:
    _parsers: dict[str, type[BaseParser]] = {
        ".pdf": PDFParser,
        ".md": MarkdownParser,
        ".markdown": MarkdownParser,
        ".txt": TXTParser,
        ".docx": DOCXParser,
        ".xlsx": ExcelParser,
        ".xls": ExcelParser,
    }

    @classmethod
    def get_parser(cls, file_path: Path) -> BaseParser:
        parser_cls = cls._parsers.get(file_path.suffix.lower())
        if parser_cls is None:
            supported = ", ".join(sorted(cls._parsers))
            raise ValueError(f"Unsupported file type '{file_path.suffix}'. Supported: {supported}")
        return parser_cls()
