"""Knowledge graph API routes."""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from src.knowledge_graph.builder import KnowledgeGraphBuilder
from src.knowledge_graph.graph_store import GraphStore
from src.knowledge_graph.merger import KnowledgeMerger
from src.knowledge_graph.models import GraphBuildResult, GraphQueryResult, KnowledgeEdge, KnowledgeNode, MergeStatus, RelationType
from src.knowledge_graph.query_engine import GraphQueryEngine


router = APIRouter(prefix="/api/graph", tags=["graph"])


class BuildGraphRequest(BaseModel):
    textbook_id: str


class GraphQueryRequest(BaseModel):
    question: str
    depth: int = 2


@router.post("/build", response_model=GraphBuildResult)
def build_graph(request: BuildGraphRequest) -> GraphBuildResult:
    store = GraphStore()
    try:
        result = KnowledgeGraphBuilder().build_from_parsed(request.textbook_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Graph build failed: {exc}") from exc
    store.upsert(result.nodes, result.edges, request.textbook_id)
    return result


@router.get("/nodes", response_model=list[KnowledgeNode])
def get_nodes(textbook_id: str | None = None) -> list[KnowledgeNode]:
    nodes = GraphStore().load_nodes()
    if textbook_id:
        nodes = [node for node in nodes if node.textbook_id == textbook_id]
    return nodes


@router.get("/edges", response_model=list[KnowledgeEdge])
def get_edges(
    textbook_id: str | None = None,
    relation_type: RelationType | None = None,
) -> list[KnowledgeEdge]:
    edges = GraphStore().load_edges()
    if textbook_id:
        edges = [edge for edge in edges if edge.textbook_id == textbook_id]
    if relation_type:
        edges = [edge for edge in edges if edge.relation_type == relation_type]
    return edges


@router.get("/search", response_model=list[KnowledgeNode])
def search_nodes(q: str = Query(min_length=1)) -> list[KnowledgeNode]:
    query = q.lower()
    return [
        node
        for node in GraphStore().load_nodes()
        if query in node.name.lower()
        or query in node.definition.lower()
        or query in node.category.lower()
    ]


@router.post("/query", response_model=GraphQueryResult)
def query_graph(request: GraphQueryRequest) -> GraphQueryResult:
    if not request.question.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question is required")
    return GraphQueryEngine().query(request.question.strip(), max(1, min(request.depth, 3)))


@router.post("/merge", response_model=MergeStatus)
def merge_graph() -> MergeStatus:
    return KnowledgeMerger().merge_cross_books()


@router.get("/merge/status", response_model=MergeStatus)
def merge_status() -> MergeStatus:
    return KnowledgeMerger().status()
