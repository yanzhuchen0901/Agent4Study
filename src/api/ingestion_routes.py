"""Ingestion API routes."""

import json
import shutil
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from src.config import get_settings
from src.ingestion.models import TextbookSchema, TextbookSummary
from src.ingestion.parser_factory import ParserFactory
from src.ingestion.utils import make_textbook_id


router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])
settings = get_settings()


def _ensure_dirs() -> None:
    settings.textbook_dir.mkdir(parents=True, exist_ok=True)
    settings.parsed_dir.mkdir(parents=True, exist_ok=True)


def _parsed_path(textbook_id: str) -> Path:
    return settings.parsed_dir / f"{textbook_id}.json"


def _load_parsed(textbook_id: str) -> dict:
    _ensure_dirs()
    parsed_path = _parsed_path(textbook_id)
    if not parsed_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Textbook not found")
    return json.loads(parsed_path.read_text(encoding="utf-8"))


@router.get("/parsed/{textbook_id}", response_model=TextbookSchema)
def get_parsed_textbook(textbook_id: str) -> TextbookSchema:
    data = _load_parsed(textbook_id)
    return TextbookSchema.model_validate(data)


@router.get("/raw/{textbook_id}")
def download_raw_textbook(textbook_id: str) -> FileResponse:
    data = _load_parsed(textbook_id)
    filename = Path(data.get("filename", "")).name
    if not filename:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raw file not found")
    raw_path = settings.textbook_dir / filename
    if not raw_path.exists() or not raw_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raw file not found")
    return FileResponse(path=raw_path, filename=filename, media_type="application/octet-stream")


@router.post("/upload", response_model=TextbookSchema)
async def upload_textbook(
    file: UploadFile = File(...),
    textbook_id: str | None = Form(default=None),
) -> TextbookSchema:
    _ensure_dirs()
    filename = Path(file.filename or "uploaded.txt").name
    raw_path = settings.textbook_dir / filename
    resolved_id = textbook_id or make_textbook_id(raw_path)
    if raw_path.exists():
        raw_path = settings.textbook_dir / f"{raw_path.stem}_{resolved_id}{raw_path.suffix}"

    with raw_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        parser = ParserFactory.get_parser(raw_path)
        textbook = parser.parse(raw_path, resolved_id)
    except ValueError as exc:
        raw_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raw_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Parse failed: {exc}") from exc

    _parsed_path(textbook.textbook_id).write_text(
        textbook.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return textbook


@router.get("/list", response_model=list[TextbookSummary])
def list_textbooks() -> list[TextbookSummary]:
    _ensure_dirs()
    summaries: list[TextbookSummary] = []
    for path in sorted(settings.parsed_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        chapters = data.get("chapters", [])
        summaries.append(
            TextbookSummary(
                textbook_id=data["textbook_id"],
                filename=data["filename"],
                title=data["title"],
                total_pages=data["total_pages"],
                total_chars=data["total_chars"],
                chapter_count=len(chapters),
            )
        )
    return summaries


@router.delete("/{textbook_id}")
def delete_textbook(textbook_id: str) -> dict:
    _ensure_dirs()
    parsed_path = _parsed_path(textbook_id)
    if not parsed_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Textbook not found")

    data = json.loads(parsed_path.read_text(encoding="utf-8"))
    parsed_path.unlink()
    raw_path = settings.textbook_dir / data.get("filename", "")
    if raw_path.exists() and raw_path.is_file():
        raw_path.unlink()

    return {"status": "deleted", "textbook_id": textbook_id}
