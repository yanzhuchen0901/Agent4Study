"""Reproducible RAG benchmark utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field
from rank_bm25 import BM25Okapi

from src.config import get_settings
from src.rag.models import Chunk
from src.rag.retriever import HybridRetriever
from src.rag.vector_store import VectorStore, tokenize


class BenchmarkCase(BaseModel):
    question: str
    expected_answer: str = ""
    expected_sources: list[str] = Field(default_factory=list)


class BenchmarkMetric(BaseModel):
    strategy: str
    chunk_size: int
    case_count: int
    hit_rate: float
    avg_retrieved: float
    estimated_prompt_tokens: int


class BenchmarkReport(BaseModel):
    status: str
    metrics: list[BenchmarkMetric]
    cases: list[BenchmarkCase]


@dataclass
class RAGBenchmark:
    """Run lightweight retrieval checks against the current local RAG index."""

    store: VectorStore | None = None

    def __post_init__(self) -> None:
        self.store = self.store or VectorStore()
        self.settings = get_settings()
        self.output_path = self.settings.data_dir / "rag_benchmark" / "benchmark_report.json"
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def default_cases(self) -> list[BenchmarkCase]:
        chunks = self.store.load_chunks()
        cases: list[BenchmarkCase] = []
        for chunk in chunks[:10]:
            tokens = tokenize(chunk.content)
            question = f"{tokens[0]} 是什么？" if tokens else f"{chunk.chapter} 的核心内容是什么？"
            cases.append(
                BenchmarkCase(
                    question=question,
                    expected_answer=chunk.content[:120],
                    expected_sources=[chunk.chunk_id],
                )
            )
        if cases:
            return cases
        return [
            BenchmarkCase(question="什么是核心概念？", expected_sources=[]),
            BenchmarkCase(question="教材知识点之间有什么关系？", expected_sources=[]),
        ]

    def run(self, cases: list[BenchmarkCase] | None = None) -> BenchmarkReport:
        cases = cases or self.default_cases()
        chunks = self.store.load_chunks()
        if not chunks:
            report = BenchmarkReport(status="empty-index", metrics=[], cases=cases)
            self._save(report)
            return report

        metrics = []
        for chunk_size in [200, 500, 800, 1200]:
            metrics.append(self._hybrid_metric(cases, chunk_size))
            metrics.append(self._bm25_metric(cases, chunks, chunk_size))
        report = BenchmarkReport(status="completed", metrics=metrics, cases=cases)
        self._save(report)
        return report

    def _hybrid_metric(self, cases: list[BenchmarkCase], chunk_size: int) -> BenchmarkMetric:
        retriever = HybridRetriever(store=self.store)
        hits = 0
        retrieved_count = 0
        token_count = 0
        for case in cases:
            retrieved = retriever.retrieve(case.question, top_k=5)
            retrieved_ids = [chunk.chunk_id for chunk, _ in retrieved]
            hits += int(not case.expected_sources or bool(set(case.expected_sources) & set(retrieved_ids)))
            retrieved_count += len(retrieved)
            token_count += sum(max(1, len(chunk.content) // 4) for chunk, _ in retrieved)
        return self._metric("hybrid-vector-bm25", chunk_size, cases, hits, retrieved_count, token_count)

    def _bm25_metric(self, cases: list[BenchmarkCase], chunks: list[Chunk], chunk_size: int) -> BenchmarkMetric:
        corpus = [tokenize(chunk.content[:chunk_size]) for chunk in chunks]
        bm25 = BM25Okapi(corpus)
        hits = 0
        retrieved_count = 0
        token_count = 0
        for case in cases:
            scores = bm25.get_scores(tokenize(case.question))
            ranked = sorted(range(len(chunks)), key=lambda index: float(scores[index]), reverse=True)[:5]
            retrieved_ids = [chunks[index].chunk_id for index in ranked]
            hits += int(not case.expected_sources or bool(set(case.expected_sources) & set(retrieved_ids)))
            retrieved_count += len(ranked)
            token_count += sum(max(1, len(chunks[index].content[:chunk_size]) // 4) for index in ranked)
        return self._metric("bm25-only", chunk_size, cases, hits, retrieved_count, token_count)

    def _metric(
        self,
        strategy: str,
        chunk_size: int,
        cases: list[BenchmarkCase],
        hits: int,
        retrieved_count: int,
        token_count: int,
    ) -> BenchmarkMetric:
        case_count = len(cases)
        return BenchmarkMetric(
            strategy=strategy,
            chunk_size=chunk_size,
            case_count=case_count,
            hit_rate=round(hits / case_count, 4) if case_count else 0.0,
            avg_retrieved=round(retrieved_count / case_count, 2) if case_count else 0.0,
            estimated_prompt_tokens=token_count,
        )

    def _save(self, report: BenchmarkReport) -> None:
        self.output_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")


def load_benchmark_report(path: Path | None = None) -> BenchmarkReport | None:
    settings = get_settings()
    report_path = path or settings.data_dir / "rag_benchmark" / "benchmark_report.json"
    if not report_path.exists():
        return None
    return BenchmarkReport.model_validate(json.loads(report_path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    result = RAGBenchmark().run()
    print(result.model_dump_json(indent=2))
