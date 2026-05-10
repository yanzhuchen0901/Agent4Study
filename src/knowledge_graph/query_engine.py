"""Natural-language graph query engine."""

from collections import deque

from src.knowledge_graph.graph_store import GraphStore
from src.knowledge_graph.llm_client import GraphLLMClient, LLMClientError
from src.knowledge_graph.models import GraphQueryResult, KnowledgeEdge, KnowledgeNode


class GraphQueryEngine:
    def __init__(self, store: GraphStore | None = None, llm_client: GraphLLMClient | None = None) -> None:
        self.store = store or GraphStore()
        self.llm_client = llm_client or GraphLLMClient()

    def query(self, question: str, depth: int = 2) -> GraphQueryResult:
        nodes = self.store.load_nodes()
        edges = self.store.load_edges()
        plan, error = self._parse_question(question, nodes)
        matched = self._match_nodes(question, nodes, plan.get("node"))

        if not matched:
            return GraphQueryResult(
                answer="未在知识图谱中找到相关知识点。",
                nodes=[],
                edges=[],
                query_type=plan["type"],
                matched_node_ids=[],
                error=error,
            )

        sub_nodes, sub_edges = self._subgraph(matched, nodes, edges, depth)
        names = "、".join(node.name for node in matched[:5])
        answer = f"已找到与“{question}”相关的知识点：{names}。子图包含 {len(sub_nodes)} 个节点和 {len(sub_edges)} 条关系。"
        return GraphQueryResult(
            answer=answer,
            nodes=sub_nodes,
            edges=sub_edges,
            query_type=plan["type"],
            matched_node_ids=[node.id for node in matched],
            error=error,
        )

    def _parse_question(self, question: str, nodes: list[KnowledgeNode]) -> tuple[dict, str | None]:
        system_prompt = "你是知识图谱查询规划助手。只输出 JSON。"
        sample_names = "、".join(node.name for node in nodes[:30])
        user_prompt = f"""
把自然语言问题转为图查询 JSON，type 只能是 neighbors/path/subgraph/search。
输出 {{"type":"neighbors","node":"概念名","relation_type":null}}
可用知识点: {sample_names}
问题: {question}
"""
        try:
            data = self.llm_client.complete_json(system_prompt, user_prompt)
            query_type = data.get("type", "search")
            if query_type not in {"neighbors", "path", "subgraph", "search"}:
                query_type = "search"
            return {"type": query_type, "node": data.get("node")}, None
        except (LLMClientError, Exception) as exc:
            return {"type": "neighbors", "node": None}, str(exc)

    def _match_nodes(self, question: str, nodes: list[KnowledgeNode], planned_node: str | None) -> list[KnowledgeNode]:
        text = (planned_node or question).lower()
        matched = [
            node
            for node in nodes
            if node.name.lower() in text
            or text in node.name.lower()
            or text in node.definition.lower()
            or text in node.category.lower()
        ]
        if matched:
            return matched[:10]
        tokens = [part for part in question.replace("？", " ").replace("?", " ").split() if len(part) >= 2]
        return [
            node
            for node in nodes
            if any(token in node.name or token in node.definition for token in tokens)
        ][:10]

    def _subgraph(
        self,
        matched: list[KnowledgeNode],
        nodes: list[KnowledgeNode],
        edges: list[KnowledgeEdge],
        depth: int,
    ) -> tuple[list[KnowledgeNode], list[KnowledgeEdge]]:
        node_by_id = {node.id: node for node in nodes}
        adjacency: dict[str, set[str]] = {}
        for edge in edges:
            adjacency.setdefault(edge.source, set()).add(edge.target)
            adjacency.setdefault(edge.target, set()).add(edge.source)

        selected_ids = {node.id for node in matched}
        queue = deque((node.id, 0) for node in matched)
        while queue:
            node_id, distance = queue.popleft()
            if distance >= depth:
                continue
            for neighbor in adjacency.get(node_id, set()):
                if neighbor not in selected_ids:
                    selected_ids.add(neighbor)
                    queue.append((neighbor, distance + 1))

        selected_edges = [
            edge for edge in edges if edge.source in selected_ids and edge.target in selected_ids
        ]
        selected_nodes = [node_by_id[node_id] for node_id in selected_ids if node_id in node_by_id]
        return selected_nodes, selected_edges
