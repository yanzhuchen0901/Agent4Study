"""Sentence-transformers embedding backend."""

from __future__ import annotations

import numpy as np

from src.config import get_settings


class Embedder:
    def __init__(self, model_name: str | None = None) -> None:
        self.settings = get_settings()
        self.model_name = (model_name or self.settings.embedding_model).strip()
        self._model = None

    def _get_model(self):
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "sentence-transformers is required for embeddings. "
                "Install it via 'pip install sentence-transformers'."
            ) from exc

        self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 0), dtype="float32")

        model = self._get_model()
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(embeddings, dtype="float32")
