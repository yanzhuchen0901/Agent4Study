"""Safe runtime settings API."""

from fastapi import APIRouter

from src.config import get_settings


router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_runtime_settings() -> dict:
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "llm_base_url": settings.llm_base_url,
        "llm_api_key_configured": bool(settings.llm_api_key),
        "embedding_provider": settings.embedding_provider,
        "embedding_model": settings.embedding_model,
        "data_dir": str(settings.data_dir),
        "textbook_dir": str(settings.textbook_dir),
        "parsed_dir": str(settings.parsed_dir),
        "chunk_dir": str(settings.chunk_dir),
        "graph_dir": str(settings.graph_dir),
    }
