"""Build knowledge nodes from parsed textbooks."""

import json
import re
from pathlib import Path

from src.config import get_settings
from src.ingestion.models import TextbookSchema
from src.knowledge_graph.llm_client import GraphLLMClient, LLMClientError
from src.knowledge_graph.models import GraphBuildResult, KnowledgeNode
from src.knowledge_graph.relation_extractor import RelationExtractor


class KnowledgeGraphBuilder:
    def __init__(self, llm_client: GraphLLMClient | None = None) -> None:
        self.settings = get_settings()
        self.llm_client = llm_client or GraphLLMClient()

    def build_from_parsed(self, textbook_id: str) -> GraphBuildResult:
        path = self.settings.parsed_dir / f"{textbook_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Parsed textbook not found: {textbook_id}")
        textbook = TextbookSchema.model_validate_json(path.read_text(encoding="utf-8"))
        return self.build(textbook)

    def build(self, textbook: TextbookSchema) -> GraphBuildResult:
        nodes: list[KnowledgeNode] = []
        for chapter in textbook.chapters:
            nodes.extend(self._extract_nodes(textbook, chapter.model_dump()))
        edges = RelationExtractor(self.llm_client).extract(textbook.textbook_id, nodes)
        return GraphBuildResult(textbook_id=textbook.textbook_id, nodes=nodes, edges=edges)

    def _extract_nodes(self, textbook: TextbookSchema, chapter: dict) -> list[KnowledgeNode]:
        content = chapter["content"][:3500]
        system_prompt = "你是教材知识图谱抽取助手。只输出 JSON。"
        few_shot = """
    示例（输入 → 输出，仅供格式参考）：

    输入:
    教材: 数据结构
    章节: 栈与队列
    正文:
    栈是一种后进先出（LIFO）的线性表。入栈称为 push，出栈称为 pop。栈常用于括号匹配与函数调用。

    输出:
    {"nodes":[
      {"name":"栈","aliases":["stack"],"definition":"后进先出（LIFO）的线性数据结构，支持push/pop操作","category":"核心概念","importance":"high","original_text":"栈是一种后进先出（LIFO）的线性表"},
      {"name":"入栈","aliases":["push"],"definition":"将元素压入栈顶的操作，常记为push","category":"方法","importance":"medium","original_text":"入栈称为push"},
      {"name":"出栈","aliases":["pop"],"definition":"从栈顶移除元素的操作，常记为pop","category":"方法","importance":"medium","original_text":"出栈称为pop"}
    ]}
    """.strip()
        user_prompt = f"""
请从教材章节中提取 3-8 个核心知识点，输出 JSON:
{{"nodes":[{{"name":"概念名","aliases":["别名"],"definition":"15-40字定义","category":"核心概念/方法/现象/定理","importance":"high/medium/low","original_text":"不超过120字原文证据"}}]}}

约束：
- 只抽取正文中有明确依据的知识点，不要凭空补充。
- aliases 只填写教材原文出现的同义名、英文缩写或常用译名。
- importance 根据教学重要性判断，核心概念为 high，普通操作/例子为 medium，边缘术语为 low。
- original_text 必须来自正文原句或短片段。

    {few_shot}

教材: {textbook.title}
章节: {chapter["title"]}
正文:
{content}
"""
        try:
            data = self.llm_client.complete_json(system_prompt, user_prompt)
            raw_nodes = data.get("nodes", [])
        except (LLMClientError, Exception):
            raw_nodes = self._rule_based_nodes(chapter["title"], content)

        nodes: list[KnowledgeNode] = []
        seen: set[str] = set()
        for item in raw_nodes[:10]:
            name = str(item.get("name", "")).strip()
            if not name or name in seen:
                continue
            seen.add(name)
            node_id = f"{textbook.textbook_id}_{chapter['chapter_id']}_node_{len(nodes)+1:03d}"
            nodes.append(
                KnowledgeNode(
                    id=node_id,
                    name=name,
                    definition=str(item.get("definition", "")).strip()[:160],
                    category=str(item.get("category", "核心概念")).strip() or "核心概念",
                    textbook_id=textbook.textbook_id,
                    textbook_title=textbook.title,
                    chapter_id=chapter["chapter_id"],
                    chapter=chapter["title"],
                    page=chapter.get("page_start", 1),
                    source_node_ids=[node_id],
                    aliases=[
                        str(alias).strip()
                        for alias in item.get("aliases", [])
                        if str(alias).strip()
                    ][:6],
                    importance=self._normalize_importance(item.get("importance")),
                    original_text=str(item.get("original_text", "")).strip()[:120],
                )
            )
        return nodes

    def _normalize_importance(self, value) -> str:
        text = str(value or "medium").strip().lower()
        if text in {"high", "medium", "low"}:
            return text
        if text in {"高", "重要", "核心"}:
            return "high"
        if text in {"低", "边缘"}:
            return "low"
        return "medium"

    def _rule_based_nodes(self, chapter_title: str, content: str) -> list[dict]:
        candidates = [chapter_title]
        candidates.extend(re.findall(r"[“\"《]?([\u4e00-\u9fffA-Za-z][\u4e00-\u9fffA-Za-z0-9]{1,18})[”\"》]?(?:是|指|包括|分为)", content))
        result = []
        for name in candidates:
            name = name.strip(" #：:，,。")
            if name and name not in {item["name"] for item in result}:
                result.append({
                    "name": name,
                    "aliases": [],
                    "definition": f"{name}相关教材知识点",
                    "category": "核心概念",
                    "importance": "medium",
                    "original_text": content[:120],
                })
            if len(result) >= 6:
                break
        return result or [{
            "name": chapter_title or "教材知识点",
            "aliases": [],
            "definition": "章节核心知识点",
            "category": "核心概念",
            "importance": "medium",
            "original_text": content[:120],
        }]
