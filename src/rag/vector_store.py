"""Persistent vector and chunk store."""

import json
import re

import numpy as np

from src.config import get_settings
from src.rag.models import Chunk


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text.lower())


class VectorStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.settings.chunk_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_path = self.settings.chunk_dir / "chunks.json"
        self.embeddings_path = self.settings.chunk_dir / "embeddings.npy"

    def save(self, chunks: list[Chunk], embeddings: np.ndarray) -> None:
        self.chunks_path.write_text(
            json.dumps([chunk.model_dump() for chunk in chunks], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        np.save(self.embeddings_path, embeddings.astype("float32"))

    def load_chunks(self) -> list[Chunk]:
        if not self.chunks_path.exists():
            return []
        return [Chunk.model_validate(item) for item in json.loads(self.chunks_path.read_text(encoding="utf-8"))]

    def load_embeddings(self) -> np.ndarray:
        if not self.embeddings_path.exists():
            return np.zeros((0, 384), dtype="float32")
        return np.load(self.embeddings_path).astype("float32")

    def status(self) -> tuple[int, int, list[str]]:
        chunks = self.load_chunks()
        embeddings = self.load_embeddings()
        return len(chunks), int(embeddings.shape[1]) if embeddings.size else 0, sorted({chunk.textbook_id for chunk in chunks})
