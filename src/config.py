"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the Agent4Study backend."""

    app_name: str = "AI Textbook Knowledge System"
    app_version: str = "0.1.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    llm_provider: str = "deepseek"
    llm_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = "https://api.deepseek.com"

    embedding_provider: str = "local"
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"

    data_dir: Path = ROOT_DIR / "data"
    textbook_dir: Path = ROOT_DIR / "data" / "textbooks"
    parsed_dir: Path = ROOT_DIR / "data" / "parsed"
    chunk_dir: Path = ROOT_DIR / "data" / "chunks"
    graph_dir: Path = ROOT_DIR / "data" / "knowledge_graph"


@lru_cache
def get_settings() -> Settings:
    data_dir = Path(os.getenv("DATA_DIR", ROOT_DIR / "data"))
    return Settings(
        app_name=os.getenv("APP_NAME", "AI Textbook Knowledge System"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("API_PORT", "8000")),
        llm_provider=os.getenv("LLM_PROVIDER", "deepseek"),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_model=os.getenv("LLM_MODEL", ""),
        llm_base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
        embedding_provider=os.getenv("EMBEDDING_PROVIDER", "local"),
        embedding_model=os.getenv(
            "EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"
        ),
        data_dir=data_dir,
        textbook_dir=Path(os.getenv("TEXTBOOK_DIR", data_dir / "textbooks")),
        parsed_dir=Path(os.getenv("PARSED_DIR", data_dir / "parsed")),
        chunk_dir=Path(os.getenv("CHUNK_DIR", data_dir / "chunks")),
        graph_dir=Path(os.getenv("GRAPH_DIR", data_dir / "knowledge_graph")),
    )
