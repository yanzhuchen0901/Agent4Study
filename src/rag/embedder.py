"""Embedding backends with a deterministic local fallback."""

import hashlib
import math
import re

import numpy as np

from src.config import get_settings


class Embedder:
    def __init__(self, dimension: int = 384) -> None:
        self.settings = get_settings()
        self.dimension = dimension

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.vstack([self._hash_embed(text) for text in texts]).astype("float32")

    def _hash_embed(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimension, dtype="float32")
        tokens = self._tokens(text)
        for token in tokens:
            digest = hashlib.md5(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(float(np.dot(vector, vector)))
        if norm > 0:
            vector /= norm
        return vector

    def _tokens(self, text: str) -> list[str]:
        words = re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text.lower())
        bigrams = [text[i : i + 2] for i in range(max(len(text) - 1, 0)) if text[i : i + 2].strip()]
        return words + bigrams[:512]
