"""Auto-generate book-level and chapter-level nodes/edges from parsed data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Set, Tuple

from src.config import get_settings
from src.ingestion.models import TextbookSchema
from src.knowledge_graph.graph_store import GraphStore
from src.knowledge_graph.models import (
    HierarchyBuildResult,
    KnowledgeEdge,
    KnowledgeNode,
)


class HierarchyBuilder:
    """Build book and chapter hierarchy from parsed textbooks and existing knowledge nodes."""

    def __init__(self, store: GraphStore | None = None) -> None:
        self.settings = get_settings()
        self.store = store or GraphStore()

    def build(self) -> HierarchyBuildResult:
        parsed_dir = self.settings.parsed_dir
        textbooks = self._load_textbooks(parsed_dir)
        knowledge_nodes = self.store.load_nodes()
        knowledge_by_tb: dict[str, list[KnowledgeNode]] = {}
        knowledge_by_ch: dict[Tuple[str, str], list[KnowledgeNode]] = {}
        for node in knowledge_nodes:
            if node.level != "knowledge":
                continue
            knowledge_by_tb.setdefault(node.textbook_id, []).append(node)
            key = (node.textbook_id, node.chapter_id)
            knowledge_by_ch.setdefault(key, []).append(node)

        book_nodes: list[KnowledgeNode] = []
        chapter_nodes: list[KnowledgeNode] = []
        all_edges: list[KnowledgeEdge] = []
        edge_counter = 0

        for tb in textbooks:
            tb_nodes = knowledge_by_tb.get(tb.textbook_id, [])
            book_id = f"book_{tb.textbook_id}"
            book_nodes.append(
                KnowledgeNode(
                    id=book_id,
                    name=tb.title or tb.textbook_id,
                    definition=f"教材《{tb.title}》，共{tb.total_pages}页，{len(tb.chapters)}章",
                    category="教材",
                    textbook_id=tb.textbook_id,
                    textbook_title=tb.title,
                    frequency=len(tb_nodes),
                    page=tb.total_pages,
                    level="book",
                )
            )

            for ch in tb.chapters:
                ch_id = f"chapter_{tb.textbook_id}_{ch.chapter_id}"
                ch_nodes_list = knowledge_by_ch.get((tb.textbook_id, ch.chapter_id), [])
                chapter_nodes.append(
                    KnowledgeNode(
                        id=ch_id,
                        name=ch.title,
                        definition=ch.content[:120].replace("\n", " ").strip(),
                        category="章节",
                        textbook_id=tb.textbook_id,
                        textbook_title=tb.title,
                        chapter_id=ch.chapter_id,
                        chapter=ch.title,
                        frequency=len(ch_nodes_list),
                        page=ch.page_start,
                        level="chapter",
                    )
                )

                edge_counter += 1
                all_edges.append(
                    KnowledgeEdge(
                        id=f"h_edge_{edge_counter:04d}",
                        source=book_id,
                        target=ch_id,
                        relation_type="contains",
                        description=f"{tb.title} 包含章节 {ch.title}",
                        textbook_id=tb.textbook_id,
                        chapter_id=ch.chapter_id,
                        level="chapter",
                    )
                )

                for kn in ch_nodes_list:
                    edge_counter += 1
                    all_edges.append(
                        KnowledgeEdge(
                            id=f"h_edge_{edge_counter:04d}",
                            source=ch_id,
                            target=kn.id,
                            relation_type="contains",
                            description=f"章节 {ch.title} 包含知识点 {kn.name}",
                            textbook_id=tb.textbook_id,
                            chapter_id=ch.chapter_id,
                            level="knowledge",
                        )
                    )

        book_book = self._build_book_edges(textbooks, knowledge_by_tb)
        for edge in book_book:
            edge_counter += 1
            edge.id = f"h_edge_{edge_counter:04d}"
        all_edges.extend(book_book)

        chapter_chapter = self._build_chapter_edges(textbooks, knowledge_by_ch)
        for edge in chapter_chapter:
            edge_counter += 1
            edge.id = f"h_edge_{edge_counter:04d}"
        all_edges.extend(chapter_chapter)

        combined_nodes = book_nodes + chapter_nodes
        self.store.upsert_level("book", combined_nodes, all_edges)

        return HierarchyBuildResult(
            book_count=len(book_nodes),
            chapter_count=len(chapter_nodes),
            book_book_edges=len(book_book),
            chapter_chapter_edges=len(chapter_chapter),
            hierarchy_edges=edge_counter,
        )

    def _load_textbooks(self, parsed_dir: Path) -> list[TextbookSchema]:
        textbooks: list[TextbookSchema] = []
        for path in sorted(parsed_dir.glob("*.json")):
            try:
                textbooks.append(
                    TextbookSchema.model_validate_json(path.read_text(encoding="utf-8"))
                )
            except Exception:
                continue
        return textbooks

    def _build_book_edges(
        self,
        textbooks: list[TextbookSchema],
        knowledge_by_tb: dict[str, list[KnowledgeNode]],
    ) -> list[KnowledgeEdge]:
        edges: list[KnowledgeEdge] = []
        tb_ids = [tb.textbook_id for tb in textbooks]
        tb_token_map: dict[str, set[str]] = {}
        for tb in textbooks:
            tokens: set[str] = set()
            for n in knowledge_by_tb.get(tb.textbook_id, []):
                tokens.update(self._tokens(n.name))
                tokens.update(self._tokens(n.definition))
            tokens.update(self._tokens(tb.title))
            tb_token_map[tb.textbook_id] = tokens

        for i in range(len(tb_ids)):
            for j in range(i + 1, len(tb_ids)):
                a, b = tb_ids[i], tb_ids[j]
                overlap, jaccard = self._jaccard(tb_token_map.get(a, set()), tb_token_map.get(b, set()))
                if jaccard >= 0.06:
                    relation = "prerequisite" if jaccard >= 0.25 else "overlap"
                    edges.append(
                        KnowledgeEdge(
                            id="",
                            source=f"book_{a}",
                            target=f"book_{b}",
                            relation_type=relation,
                            description=(
                                f"共享 {overlap} 个关键词 (Jaccard={jaccard:.2f})"
                            ),
                            level="book",
                        )
                    )
        return edges

    def _build_chapter_edges(
        self,
        textbooks: list[TextbookSchema],
        knowledge_by_ch: dict[Tuple[str, str], list[KnowledgeNode]],
    ) -> list[KnowledgeEdge]:
        edges: list[KnowledgeEdge] = []
        tb_map = {tb.textbook_id: tb for tb in textbooks}
        ch_token_map: dict[Tuple[str, str], set[str]] = {}

        for key, nodes in knowledge_by_ch.items():
            tokens: set[str] = set()
            for n in nodes:
                tokens.update(self._tokens(n.name))
                tokens.update(self._tokens(n.definition))
            tb = tb_map.get(key[0])
            if tb:
                ch = next((c for c in tb.chapters if c.chapter_id == key[1]), None)
                if ch:
                    tokens.update(self._tokens(ch.title))
            ch_token_map[key] = tokens

        ch_keys = list(knowledge_by_ch.keys())
        for i in range(len(ch_keys)):
            for j in range(i + 1, len(ch_keys)):
                key_a, key_b = ch_keys[i], ch_keys[j]
                if key_a[0] == key_b[0]:
                    continue
                overlap, jaccard = self._jaccard(ch_token_map.get(key_a, set()), ch_token_map.get(key_b, set()))
                if jaccard >= 0.06:
                    ch_a_id = f"chapter_{key_a[0]}_{key_a[1]}"
                    ch_b_id = f"chapter_{key_b[0]}_{key_b[1]}"
                    relation = "prerequisite" if jaccard >= 0.25 else "overlap"
                    edges.append(
                        KnowledgeEdge(
                            id="",
                            source=ch_a_id,
                            target=ch_b_id,
                            relation_type=relation,
                            description=(
                                f"共享 {overlap} 个关键词 (Jaccard={jaccard:.2f})"
                            ),
                            level="chapter",
                        )
                    )
        return edges

    @staticmethod
    def _tokens(text: str) -> list[str]:
        import re
        text = text.lower()
        eng_tokens = re.findall(r"[a-z]+", text)
        chn_chars = re.findall(r"[\u4e00-\u9fff]", text)
        return eng_tokens + chn_chars

    @staticmethod
    def _jaccard(a: set[str], b: set[str]) -> Tuple[int, float]:
        inter = a & b
        union = a | b
        if not union:
            return 0, 0.0
        return len(inter), round(len(inter) / len(union), 4)
