"""Hybrid vector + BM25 retrieval."""

from rank_bm25 import BM25Okapi

from src.rag.embedder import Embedder
from src.rag.models import Chunk
from src.rag.vector_store import VectorStore, tokenize


class HybridRetriever:
    def __init__(self, store: VectorStore | None = None, embedder: Embedder | None = None) -> None:
        self.store = store or VectorStore()
        self.embedder = embedder or Embedder()

    def retrieve(self, query: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
        chunks = self.store.load_chunks()
        embeddings = self.store.load_embeddings()
        if not chunks or embeddings.size == 0:
            return []

        query_vector = self.embedder.encode([query])[0]
        vector_scores = embeddings @ query_vector
        vector_rank = sorted(range(len(chunks)), key=lambda i: float(vector_scores[i]), reverse=True)[:10]

        tokenized = [tokenize(chunk.content) for chunk in chunks]
        bm25 = BM25Okapi(tokenized)
        bm25_scores = bm25.get_scores(tokenize(query))
        bm25_rank = sorted(range(len(chunks)), key=lambda i: float(bm25_scores[i]), reverse=True)[:10]

        fused: dict[int, float] = {}
        for rank, index in enumerate(vector_rank):
            fused[index] = fused.get(index, 0.0) + 0.7 / (rank + 1)
        for rank, index in enumerate(bm25_rank):
            fused[index] = fused.get(index, 0.0) + 0.3 / (rank + 1)

        ranked = sorted(fused.items(), key=lambda item: item[1], reverse=True)[:top_k]
        best = ranked[0][1] if ranked else 1.0
        return [(chunks[index], min(score / best, 1.0)) for index, score in ranked]
