"""Knowledge graph data models."""

from typing import Literal

from pydantic import BaseModel, Field


RelationType = Literal["prerequisite", "parallel", "contains", "applies_to", "overlap"]
MergeAction = Literal["merge", "keep", "remove"]


class KnowledgeNode(BaseModel):
    id: str
    name: str
    definition: str = ""
    category: str = "核心概念"
    textbook_id: str = ""
    textbook_title: str = ""
    chapter_id: str = ""
    chapter: str = ""
    page: int = 1
    frequency: int = 1
    source_node_ids: list[str] = Field(default_factory=list)
    level: str = "knowledge"


class KnowledgeEdge(BaseModel):
    id: str
    source: str
    target: str
    relation_type: RelationType
    description: str = ""
    textbook_id: str = ""
    chapter_id: str = ""
    level: str = "knowledge"


class MergeDecision(BaseModel):
    decision_id: str
    action: MergeAction
    affected_nodes: list[str]
    result_node: str | None = None
    reason: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class GraphBuildResult(BaseModel):
    textbook_id: str
    nodes: list[KnowledgeNode]
    edges: list[KnowledgeEdge]


class MergeStatus(BaseModel):
    node_count: int
    edge_count: int
    merge_decision_count: int
    deduplication_rate: float
    decisions: list[MergeDecision]


class GraphQueryResult(BaseModel):
    answer: str
    nodes: list[KnowledgeNode]
    edges: list[KnowledgeEdge]
    query_type: str
    matched_node_ids: list[str]
    error: str | None = None
