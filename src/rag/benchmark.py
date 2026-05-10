"""Small benchmark scaffold for later Task 8 reporting."""

from pydantic import BaseModel


class BenchmarkCase(BaseModel):
    question: str
    expected_answer: str = ""
    expected_sources: list[str] = []


class RAGBenchmark:
    def run(self, cases: list[BenchmarkCase]) -> dict:
        return {"cases": len(cases), "status": "placeholder"}
