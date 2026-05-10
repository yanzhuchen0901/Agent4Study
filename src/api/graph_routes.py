"""Knowledge graph API routes."""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from src.knowledge_graph.builder import KnowledgeGraphBuilder
from src.knowledge_graph.graph_store import GraphStore
from src.knowledge_graph.llm_client import GraphLLMClient
from src.knowledge_graph.merger import KnowledgeMerger
from src.knowledge_graph.models import GraphBuildResult, GraphQueryResult, KnowledgeEdge, KnowledgeNode, MergeStatus, RelationType
from src.knowledge_graph.query_engine import GraphQueryEngine


router = APIRouter(prefix="/api/graph", tags=["graph"])


class LLMConfig(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None


class BuildGraphRequest(BaseModel):
    textbook_id: str
    llm_config: LLMConfig | None = None


class GraphQueryRequest(BaseModel):
    question: str
    depth: int = 2
    llm_config: LLMConfig | None = None


class MergeReview(BaseModel):
    decision_id: str
    action: str
    approved: bool = True


class MergeConfirmRequest(BaseModel):
    decisions: list[MergeReview]
    llm_config: LLMConfig | None = None


class MergeRequest(BaseModel):
    llm_config: LLMConfig | None = None


@router.post("/build", response_model=GraphBuildResult)
def build_graph(request: BuildGraphRequest) -> GraphBuildResult:
    store = GraphStore()
    try:
        llm_client = GraphLLMClient(request.llm_config.model_dump(exclude_none=True)) if request.llm_config else None
        result = KnowledgeGraphBuilder(llm_client=llm_client).build_from_parsed(request.textbook_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Graph build failed: {exc}") from exc
    store.upsert(result.nodes, result.edges, request.textbook_id)
    return result


@router.get("/nodes", response_model=list[KnowledgeNode])
def get_nodes(
    textbook_id: str | None = None,
    chapter_id: str | None = None,
    level: str | None = None,
) -> list[KnowledgeNode]:
    nodes = GraphStore().load_nodes()
    if textbook_id:
        nodes = [node for node in nodes if node.textbook_id == textbook_id]
    if chapter_id:
        nodes = [node for node in nodes if node.chapter_id == chapter_id]
    if level:
        nodes = [node for node in nodes if node.level == level]
    return nodes


@router.get("/edges", response_model=list[KnowledgeEdge])
def get_edges(
    textbook_id: str | None = None,
    relation_type: RelationType | None = None,
    level: str | None = None,
) -> list[KnowledgeEdge]:
    edges = GraphStore().load_edges()
    if textbook_id:
        edges = [edge for edge in edges if edge.textbook_id == textbook_id]
    if relation_type:
        edges = [edge for edge in edges if edge.relation_type == relation_type]
    if level:
        edges = [edge for edge in edges if getattr(edge, 'level', 'knowledge') == level]
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
        or query in node.original_text.lower()
        or any(query in alias.lower() for alias in node.aliases)
    ]


@router.post("/query", response_model=GraphQueryResult)
def query_graph(request: GraphQueryRequest) -> GraphQueryResult:
    if not request.question.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question is required")
    llm_client = GraphLLMClient(request.llm_config.model_dump(exclude_none=True)) if request.llm_config else None
    return GraphQueryEngine(llm_client=llm_client).query(request.question.strip(), max(1, min(request.depth, 3)))


@router.post("/merge", response_model=MergeStatus)
def merge_graph(request: MergeRequest | None = None) -> MergeStatus:
    llm_client = GraphLLMClient(request.llm_config.model_dump(exclude_none=True)) if request and request.llm_config else None
    return KnowledgeMerger(llm_client=llm_client).merge_cross_books()


@router.post("/merge/preview", response_model=MergeStatus)
def preview_merge(request: MergeRequest | None = None) -> MergeStatus:
    llm_client = GraphLLMClient(request.llm_config.model_dump(exclude_none=True)) if request and request.llm_config else None
    return KnowledgeMerger(llm_client=llm_client).preview()


@router.post("/merge/confirm", response_model=MergeStatus)
def confirm_merge(request: MergeConfirmRequest) -> MergeStatus:
    llm_client = GraphLLMClient(request.llm_config.model_dump(exclude_none=True)) if request.llm_config else None
    return KnowledgeMerger(llm_client=llm_client).confirm([review.model_dump() for review in request.decisions])


@router.get("/merge/status", response_model=MergeStatus)
def merge_status() -> MergeStatus:
    return KnowledgeMerger().status()
