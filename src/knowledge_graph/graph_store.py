"""Persistent NetworkX-backed graph store."""

import json
from pathlib import Path

import networkx as nx

from src.config import get_settings
from src.knowledge_graph.models import KnowledgeEdge, KnowledgeNode


class GraphStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.settings.graph_dir.mkdir(parents=True, exist_ok=True)
        self.nodes_path = self.settings.graph_dir / "nodes.json"
        self.edges_path = self.settings.graph_dir / "edges.json"

    def load_nodes(self) -> list[KnowledgeNode]:
        if not self.nodes_path.exists():
            return []
        return [KnowledgeNode.model_validate(item) for item in json.loads(self.nodes_path.read_text(encoding="utf-8"))]

    def load_edges(self) -> list[KnowledgeEdge]:
        if not self.edges_path.exists():
            return []
        return [KnowledgeEdge.model_validate(item) for item in json.loads(self.edges_path.read_text(encoding="utf-8"))]

    def save(self, nodes: list[KnowledgeNode], edges: list[KnowledgeEdge]) -> None:
        self.nodes_path.write_text(json.dumps([node.model_dump() for node in nodes], ensure_ascii=False, indent=2), encoding="utf-8")
        self.edges_path.write_text(json.dumps([edge.model_dump() for edge in edges], ensure_ascii=False, indent=2), encoding="utf-8")

    def upsert(self, new_nodes: list[KnowledgeNode], new_edges: list[KnowledgeEdge], textbook_id: str | None = None) -> None:
        nodes = [node for node in self.load_nodes() if textbook_id is None or node.textbook_id != textbook_id]
        edges = [edge for edge in self.load_edges() if textbook_id is None or edge.textbook_id != textbook_id]
        node_by_id = {node.id: node for node in nodes + new_nodes}
        edge_by_id = {edge.id: edge for edge in edges + new_edges}
        self.save(list(node_by_id.values()), list(edge_by_id.values()))

    def as_networkx(self) -> nx.DiGraph:
        graph = nx.DiGraph()
        for node in self.load_nodes():
            graph.add_node(node.id, **node.model_dump())
        for edge in self.load_edges():
            graph.add_edge(edge.source, edge.target, **edge.model_dump())
        return graph
