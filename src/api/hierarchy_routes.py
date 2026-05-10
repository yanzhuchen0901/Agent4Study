"""Hierarchy build and summary API routes."""

from fastapi import APIRouter

from src.knowledge_graph.graph_store import GraphStore
from src.knowledge_graph.hierarchy_builder import HierarchyBuilder
from src.knowledge_graph.models import HierarchyBuildResult


router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.post("/hierarchy/build", response_model=HierarchyBuildResult)
def build_hierarchy() -> HierarchyBuildResult:
    store = GraphStore()
    return HierarchyBuilder(store=store).build()


@router.get("/hierarchy/summary")
def hierarchy_summary() -> dict:
    store = GraphStore()
    nodes = store.load_nodes()
    edges = store.load_edges()
    return {
        "book": {
            "nodes": sum(1 for n in nodes if n.level == "book"),
            "edges": sum(1 for e in edges if getattr(e, "level", "knowledge") == "book"),
        },
        "chapter": {
            "nodes": sum(1 for n in nodes if n.level == "chapter"),
            "edges": sum(1 for e in edges if getattr(e, "level", "knowledge") == "chapter"),
        },
        "knowledge": {
            "nodes": sum(1 for n in nodes if n.level == "knowledge"),
            "edges": sum(1 for e in edges if getattr(e, "level", "knowledge") == "knowledge"),
        },
    }
