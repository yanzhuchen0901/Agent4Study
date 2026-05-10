"""PDF textbook parser with OCR fallback for scanned documents."""

from pathlib import Path

import fitz

from src.ingestion import BaseParser
from src.ingestion.models import ChapterSchema, TextbookSchema
from src.ingestion.utils import build_textbook, make_chapter, split_text_into_chapters

# Threshold (average chars per page) below which OCR is triggered.
# Text-based PDFs typically yield thousands of chars per page;
# scanned PDFs yield 0 or just a handful of garbage chars.
_OCR_THRESHOLD = 50

_reader = None


def _lazy_reader():
    """Return a module-level EasyOCR reader, initialised once on first use."""
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(["ch_sim", "en"], gpu=False)
    return _reader


class PDFParser(BaseParser):
    def parse(self, file_path: Path, textbook_id: str | None = None) -> TextbookSchema:
        with fitz.open(file_path) as document:
            title = document.metadata.get("title") or file_path.stem
            page_texts = [page.get_text("text") for page in document]
            total_pages = document.page_count
            toc = document.get_toc(simple=True)

        total_chars = sum(len(t.strip()) for t in page_texts)

        # If the average text per page is too low, the PDF is likely scanned —
        # fall back to OCR.
        if total_pages > 0 and total_chars // total_pages < _OCR_THRESHOLD:
            page_texts = self._ocr_pages(file_path)
            total_chars = sum(len(t.strip()) for t in page_texts)

        if toc:
            chapters = self._chapters_from_toc(toc, page_texts)
        else:
            chapters = split_text_into_chapters("\n\n".join(page_texts), file_path.stem, 1, total_pages)

        return build_textbook(file_path, textbook_id, title, total_pages, chapters)

    def _ocr_pages(self, file_path: str | Path) -> list[str]:
        """Render every PDF page to an image and run EasyOCR."""
        reader = _lazy_reader()
        page_texts: list[str] = []
        with fitz.open(file_path) as document:
            for page in document:
                pix = page.get_pixmap(dpi=300)
                img_bytes = pix.tobytes("png")
                results = reader.readtext(img_bytes)
                # results: list of (bbox, text, confidence)
                page_text = " ".join(r[1] for r in results)
                page_texts.append(page_text)
        return page_texts

    def _chapters_from_toc(self, toc: list[list], page_texts: list[str]) -> list[ChapterSchema]:
        top_items = [(title, page) for level, title, page in toc if level == 1]
        if not top_items:
            top_items = [(title, page) for level, title, page in toc if level <= 2]
        if not top_items:
            return split_text_into_chapters("\n\n".join(page_texts), "正文", 1, len(page_texts))

        chapters: list[ChapterSchema] = []
        for index, (title, page_start) in enumerate(top_items, 1):
            next_start = top_items[index][1] if index < len(top_items) else len(page_texts) + 1
            start = max(page_start, 1)
            end = max(next_start - 1, start)
            content = "\n\n".join(page_texts[start - 1 : end])
            chapters.append(make_chapter(index, title, content, start, end))
        return chapters
