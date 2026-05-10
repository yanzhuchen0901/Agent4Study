"""Agents that call RAG and knowledge graph tools."""

from src.agent import BaseAgent
from src.knowledge_graph.query_engine import GraphQueryEngine
from src.rag.generator import RAGGenerator
from src.rag.retriever import HybridRetriever


class SearcherAgent(BaseAgent):
    name = "Searcher"

    def run(self, query: str) -> dict:
        retrieved = HybridRetriever().retrieve(query, top_k=5)
        result = RAGGenerator().generate(query, retrieved)
        return result.model_dump()


class KnowledgeGraphAgent(BaseAgent):
    name = "KnowledgeGraph"

    def run(self, query: str) -> dict:
        return GraphQueryEngine().query(query).model_dump()
