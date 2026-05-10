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
            system_prompt = "你是教材问答助手。只基于给定上下文回答，输出 JSON。"
            few_shot = """
示例（输入 → 输出，仅供格式参考）：

问题: 什么是栈？
上下文:
[1] 数据结构 栈与队列 p.10
栈是一种后进先出（LIFO）的线性表，支持push和pop操作。

输出:
{"answer":"栈是后进先出（LIFO）的线性数据结构，支持push/pop操作。[1]","used_sources":[1]}
""".strip()
            user_prompt = (
                f"问题: {query}\n"
                f"上下文:\n{context}\n\n"
                f"{few_shot}\n\n"
                "约束：如果上下文没有足够证据，回答“教材中未找到相关信息”，不要补充常识。"
                "每个关键论断都必须带[来源序号]。\n"
                "输出 {\"answer\":\"回答，必须带[来源序号]\",\"used_sources\":[1,2]}"
            )
            data = self.llm_client.complete_json(system_prompt, user_prompt)
            answer = str(data.get("answer", "")).strip()
            if answer:
                return RAGQueryResult(answer=answer, citations=citations, source_chunks=source_chunks)
        except (LLMClientError, Exception):
            pass

        lead = retrieved[0][0]
        answer = f"{lead.content[:260]} [来源：《{lead.textbook_title}》{lead.chapter} 第{lead.page}页]"
        return RAGQueryResult(answer=answer, citations=citations, source_chunks=source_chunks)
