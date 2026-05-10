"""Cross-textbook knowledge node merge."""

import json
import re
from difflib import SequenceMatcher

from src.config import get_settings
from src.knowledge_graph.graph_store import GraphStore
from src.knowledge_graph.llm_client import GraphLLMClient, LLMClientError
from src.knowledge_graph.models import KnowledgeEdge, KnowledgeNode, MergeDecision, MergeStatus


def normalize_name(name: str) -> str:
    return re.sub(r"[\s\-_/（）()《》“”\"']", "", name).lower()


class KnowledgeMerger:
    def __init__(self, store: GraphStore | None = None, llm_client: GraphLLMClient | None = None) -> None:
        self.settings = get_settings()
        self.store = store or GraphStore()
        self.llm_client = llm_client or GraphLLMClient()
        self.decisions_path = self.settings.graph_dir / "merge_decisions.json"

    def merge_cross_books(self) -> MergeStatus:
        nodes = self.store.load_nodes()
        edges = self.store.load_edges()
        original_count = len(nodes)
        groups = self._candidate_groups(nodes)
        decisions: list[MergeDecision] = []

        for group in groups:
            decision = self._decide(group, len(decisions) + 1)
            decisions.append(decision)
            if decision.action == "merge" and len(group) > 1:
                nodes, edges = self._apply_merge(nodes, edges, group, decision)

        self.store.save(nodes, edges)
        self.decisions_path.write_text(json.dumps([d.model_dump() for d in decisions], ensure_ascii=False, indent=2), encoding="utf-8")
        return self.status(original_count=original_count)

    def status(self, original_count: int | None = None) -> MergeStatus:
        nodes = self.store.load_nodes()
        edges = self.store.load_edges()
        decisions = self._load_decisions()
        merge_count = sum(1 for decision in decisions if decision.action == "merge")
        baseline = original_count or (len(nodes) + merge_count)
        rate = 0.0 if baseline == 0 else round((baseline - len(nodes)) / baseline, 4)
        return MergeStatus(
            node_count=len(nodes),
            edge_count=len(edges),
            merge_decision_count=len(decisions),
            deduplication_rate=max(rate, 0.0),
            decisions=decisions,
        )

    def _load_decisions(self) -> list[MergeDecision]:
        if not self.decisions_path.exists():
            return []
        return [MergeDecision.model_validate(item) for item in json.loads(self.decisions_path.read_text(encoding="utf-8"))]

    def _candidate_groups(self, nodes: list[KnowledgeNode]) -> list[list[KnowledgeNode]]:
        used: set[str] = set()
        groups: list[list[KnowledgeNode]] = []
        for node in nodes:
            if node.id in used:
                continue
            group = [node]
            for other in nodes:
                if other.id == node.id or other.id in used:
                    continue
                same_textbook = other.textbook_id == node.textbook_id
                name_score = SequenceMatcher(None, normalize_name(node.name), normalize_name(other.name)).ratio()
                def_score = SequenceMatcher(None, node.definition, other.definition).ratio()
                if not same_textbook and (name_score >= 0.86 or def_score >= 0.72):
                    group.append(other)
            if len(group) > 1:
                used.update(item.id for item in group)
                groups.append(group)
        return groups

    def _decide(self, group: list[KnowledgeNode], index: int) -> MergeDecision:
        affected = [node.id for node in group]
        system_prompt = "你是跨教材知识点合并裁决助手。只输出 JSON。"
        user_prompt = "\n".join([f"- {node.id}: {node.name} / {node.definition} / {node.textbook_title}" for node in group])
        user_prompt += '\n输出 {"action":"merge|keep|remove","reason":"原因","confidence":0.0}'
        try:
            data = self.llm_client.complete_json(system_prompt, user_prompt)
            action = data.get("action", "merge")
            if action not in {"merge", "keep", "remove"}:
                action = "merge"
            reason = str(data.get("reason", "语义高度相似，建议合并"))
            confidence = float(data.get("confidence", 0.85))
        except (LLMClientError, Exception):
            action, reason, confidence = "merge", "名称或定义相似，按规则合并", 0.78
        return MergeDecision(
            decision_id=f"merge_{index:03d}",
            action=action,
            affected_nodes=affected,
            result_node=affected[0] if action == "merge" else None,
            reason=reason,
            confidence=max(0.0, min(confidence, 1.0)),
        )

    def _apply_merge(
        self,
        nodes: list[KnowledgeNode],
        edges: list[KnowledgeEdge],
        group: list[KnowledgeNode],
        decision: MergeDecision,
    ) -> tuple[list[KnowledgeNode], list[KnowledgeEdge]]:
        result_id = decision.result_node or group[0].id
        group_ids = {node.id for node in group}
        primary = group[0].model_copy(deep=True)
        primary.id = result_id
        primary.frequency = sum(node.frequency for node in group)
        primary.source_node_ids = sorted({source for node in group for source in (node.source_node_ids or [node.id])})
        primary.definition = max((node.definition for node in group), key=len, default=primary.definition)

        remaining = [node for node in nodes if node.id not in group_ids]
        remaining.append(primary)

        rewritten: dict[str, KnowledgeEdge] = {}
        for edge in edges:
            source = result_id if edge.source in group_ids else edge.source
            target = result_id if edge.target in group_ids else edge.target
            if source == target:
                continue
            updated = edge.model_copy(update={"source": source, "target": target})
            rewritten[f"{source}:{target}:{updated.relation_type}"] = updated
        return remaining, list(rewritten.values())
