"""Extract graph edges between nearby knowledge nodes."""

from itertools import combinations

from src.knowledge_graph.llm_client import GraphLLMClient, LLMClientError
from src.knowledge_graph.models import KnowledgeEdge, KnowledgeNode, RelationType


class RelationExtractor:
    def __init__(self, llm_client: GraphLLMClient | None = None) -> None:
        self.llm_client = llm_client or GraphLLMClient()

    def extract(self, textbook_id: str, nodes: list[KnowledgeNode]) -> list[KnowledgeEdge]:
        edges: list[KnowledgeEdge] = []
        by_chapter: dict[str, list[KnowledgeNode]] = {}
        for node in nodes:
            by_chapter.setdefault(node.chapter_id, []).append(node)

        for chapter_id, chapter_nodes in by_chapter.items():
            for source, target in list(combinations(chapter_nodes, 2))[:20]:
                relation = self._decide_relation(source, target)
                edge_id = f"{textbook_id}_{chapter_id}_edge_{len(edges)+1:03d}"
                edges.append(
                    KnowledgeEdge(
                        id=edge_id,
                        source=source.id,
                        target=target.id,
                        relation_type=relation,
                        description=f"{source.name} 与 {target.name} 存在 {relation} 关系",
                        textbook_id=textbook_id,
                        chapter_id=chapter_id,
                    )
                )
        return edges

    def _decide_relation(self, source: KnowledgeNode, target: KnowledgeNode) -> RelationType:
        system_prompt = "你是知识图谱关系分类助手。只输出 JSON。"
        few_shot = """
    示例（关系类型必须是 prerequisite/parallel/contains/applies_to）：

    1) prerequisite（先修）
    输入: A=微积分, B=梯度下降
    输出: {"relation_type":"prerequisite","description":"理解梯度下降需要微积分基础"}

    2) contains（包含）
    输入: A=排序算法, B=快速排序
    输出: {"relation_type":"contains","description":"快速排序属于排序算法的一种"}

    3) applies_to（应用于）
    输入: A=动态规划, B=最短路径
    输出: {"relation_type":"applies_to","description":"动态规划可用于某些最短路径问题求解"}

    4) parallel（并列/相关）
    输入: A=队列, B=栈
    输出: {"relation_type":"parallel","description":"二者都是线性结构，场景不同但可对比"}
    """.strip()
        user_prompt = f"""
判断两个概念关系，relation_type 只能是 prerequisite/parallel/contains/applies_to。
输出 {{"relation_type":"parallel","description":"原因"}}

    {few_shot}

A: {source.name} - {source.definition}
B: {target.name} - {target.definition}
"""
        try:
            data = self.llm_client.complete_json(system_prompt, user_prompt)
            relation = data.get("relation_type", "parallel")
            if relation in {"prerequisite", "parallel", "contains", "applies_to"}:
                return relation
        except (LLMClientError, Exception):
            pass
        if source.name in target.definition:
            return "prerequisite"
        if target.name in source.definition:
            return "contains"
        return "parallel"
