"""RAG answer generation with citations."""

from src.knowledge_graph.llm_client import GraphLLMClient, LLMClientError
from src.rag.models import Citation, Chunk, RAGQueryResult


class RAGGenerator:
    def __init__(self, llm_client: GraphLLMClient | None = None) -> None:
        self.llm_client = llm_client or GraphLLMClient()

    def generate(self, query: str, retrieved: list[tuple[Chunk, float]]) -> RAGQueryResult:
        if not retrieved:
            return RAGQueryResult(answer="当前知识库中未找到相关信息", citations=[], source_chunks=[])

        citations = [
            Citation(
                textbook=chunk.textbook_title,
                chapter=chunk.chapter,
                page=chunk.page,
                relevance_score=round(score, 4),
                chunk_id=chunk.chunk_id,
            )
            for chunk, score in retrieved
        ]
        source_chunks = [chunk.content for chunk, _ in retrieved]
        context = "\n\n".join(
            f"[{i+1}] {chunk.textbook_title} {chunk.chapter} p.{chunk.page}\n{chunk.content}"
            for i, (chunk, _) in enumerate(retrieved)
        )
        try:
            data = self.llm_client.complete_json(
                "你是教材问答助手。只基于给定上下文回答，输出 JSON。",
                f'问题: {query}\n上下文:\n{context}\n输出 {{"answer":"回答，必须带[来源序号]","used_sources":[1,2]}}',
            )
            answer = str(data.get("answer", "")).strip()
            if answer:
                return RAGQueryResult(answer=answer, citations=citations, source_chunks=source_chunks)
        except (LLMClientError, Exception):
            pass

        lead = retrieved[0][0]
        answer = f"{lead.content[:260]} [来源：《{lead.textbook_title}》{lead.chapter} 第{lead.page}页]"
        return RAGQueryResult(answer=answer, citations=citations, source_chunks=source_chunks)
