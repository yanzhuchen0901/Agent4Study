"""Agents that call RAG and knowledge graph tools."""

from src.agent import BaseAgent
from src.knowledge_graph.llm_client import GraphLLMClient
from src.knowledge_graph.query_engine import GraphQueryEngine
from src.rag.generator import RAGGenerator
from src.rag.retriever import HybridRetriever


class SearcherAgent(BaseAgent):
    name = "Searcher"

    def __init__(self, llm_client: GraphLLMClient | None = None) -> None:
        self.llm_client = llm_client

    def run(self, query: str) -> dict:
        retrieved = HybridRetriever().retrieve(query, top_k=5)
        result = RAGGenerator(llm_client=self.llm_client).generate(query, retrieved)
        return result.model_dump()


class KnowledgeGraphAgent(BaseAgent):
    name = "KnowledgeGraph"

    def __init__(self, llm_client: GraphLLMClient | None = None) -> None:
        self.llm_client = llm_client

    def run(self, query: str) -> dict:
        return GraphQueryEngine(llm_client=self.llm_client).query(query).model_dump()
