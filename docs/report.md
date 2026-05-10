# Agent4Study 竞赛报告

生成时间：2026-05-10 13:35

## 1. Abstract

Agent4Study 是一个面向多教材学习场景的 AI 全栈系统，覆盖教材解析、知识图谱构建、跨教材知识合并、RAG 问答、自然语言图查询和多 Agent 综合推理。系统以 FastAPI + Vue 3 为基础，后端复用统一解析产物和图谱/RAG 存储，前端通过六个 Tab 提供完整交互入口。

## 2. Problem Statement

多本教材之间经常存在概念重复、定义差异、章节组织不一致和知识关系隐含的问题。传统检索只能返回片段，难以回答跨章节、跨教材和需要推理的问题。本项目目标是把教材内容转化为可检索、可合并、可解释的知识系统，并为学习者提供图谱探索、RAG 问答和 Agent 工作流。

## 3. Proposed Approach

- 教材解析：将 PDF、Markdown、TXT、DOCX、Excel 统一解析为 `data/parsed/*.json`。
- 知识图谱：抽取知识节点和关系，持久化为 `nodes.json` / `edges.json`，支持搜索、自然语言查询和跨教材合并。
- RAG：基于 chunk、embedding、向量相似度和 BM25 融合检索生成带引用回答。
- Agent：Decomposer、Planner、Searcher、KG Agent、Synthesizer 协同工作，SSE 实时展示执行过程。
- UI：Vue 3 + Vite 提供图谱、RAG、合并、Agent、报告和设置六个主要工作区。

## 4. Experiments & Results

### 4.1 Current Data Snapshot

| Metric | Value |
| --- | ---: |
| Parsed textbook ids in RAG index | 1 |
| RAG chunks | 5 |
| Embedding dimension | 384 |
| Knowledge graph nodes | 20 |
| Knowledge graph edges | 30 |
| Merge decisions | 3 |
| Estimated deduplication rate | 13.04% |

### 4.2 RAG Chunk Size 对比

当前未检测到可评测索引。运行 `python -m src.rag.benchmark` 后会生成可复现指标。

### 4.3 Hybrid vs 纯 BM25 检索

Benchmark 同时记录 `hybrid-vector-bm25` 与 `bm25-only`。在已有索引时，命中率和 token 估算可复现写入 `data/rag_benchmark/benchmark_report.json`；无索引时报告保持 `empty-index` 状态，等待教材数据导入后重新运行。

### 4.4 Agent 消融实验

当前 Agent 采用 RAG 与知识图谱双通道。RAG 提供原文证据和引用，图谱查询提供概念关系、邻居和子图上下文；Synthesizer 汇总两类证据。后续可在相同问题集上关闭图谱或关闭 RAG，比较引用覆盖率、回答完整性和推理链可解释性。

### 4.5 Prompt 策略对比

系统将节点抽取、关系抽取、合并判断、图查询解析拆分为独立 prompt。失败时使用规则回退，避免单个 LLM 调用失败导致整体功能不可用。

## 5. Limitations & Future Work

- Benchmark 当前以本地索引和轻量 ground truth 为主，正式评测应补充人工标注 Q&A。
- 图谱合并已支持人工确认，但复杂 diff 和版本回滚仍可继续增强。
- Docker 已覆盖一键开发/演示部署，生产环境可继续拆分持久化存储、反向代理和模型服务。
- 多模态图片/表格理解、rerank、Ollama 本地模型可作为后续 P1 扩展。

## 6. References

- FastAPI: backend API and OpenAPI documentation.
- Vue 3 + Vite: frontend SPA.
- NetworkX: graph storage and traversal.
- sentence-transformers / FAISS / BM25: retrieval foundation.
- DeepSeek OpenAI-compatible API: LLM extraction and generation.
