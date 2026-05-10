# AI 全栈黑客松 — 8 阶段任务拆解与执行计划

> 依据 `AI全栈黑客松_开发方案_v1.md` 开发规范制定
> 每个 Task 必须完成前提 Task 后方可开始

---

## 依赖关系总图

```
Task 1 (项目骨架)
   │
   ▼
Task 2 (数据解析)
   │
   ├──────────────┐
   ▼              ▼
Task 3 (图谱构建)   Task 5 (RAG Pipeline)
   │              │
   ▼              ▼
Task 4 (图谱可视化)  Task 6 (Agent 系统)
   │              │
   └──────┬───────┘
          ▼
      Task 7 (UI 整合)
          │
          ▼
      Task 8 (文档/报告/Docker)
```

---

## Task 1: 项目骨架与基础设施搭建

**前提 Task:** 无

**目标:** 搭建完整的前后端项目结构、配置、CI/CD 流水线

### Plan 1.1 — 后端 FastAPI 项目初始化

| 步骤 | 操作 | 文件 |
|------|------|------|
| 1.1.1 | 创建项目根目录及 `src/` 子目录 | `textbook-knowledge-system/` |
| 1.1.2 | 编写 `requirements.txt` | FastAPI, uvicorn, PyMuPDF, python-docx, pandas, openpyxl, sentence-transformers, faiss-cpu, networkx, openai, langgraph, python-multipart, pydantic |
| 1.1.3 | 创建 `src/config.py` | 加载 `.env` 配置（LLM API Key, 模型名, 路径等） |
| 1.1.4 | 创建 `src/main.py` | FastAPI app 实例 + CORS 中间件 + 生命周期管理 |
| 1.1.5 | 创建 `src/__init__.py` | 包初始化 |
| 1.1.6 | 创建 `.env.example` | 所有环境变量模板 |
| 1.1.7 | 创建 `.gitignore` | 含 `*.pdf`, `data/`, `__pycache__`, `.env` |

### Plan 1.2 — 前端 Vue 3 项目初始化

| 步骤 | 操作 | 文件 |
|------|------|------|
| 1.2.1 | `npm create vite@latest frontend -- --template vue` | `frontend/` |
| 1.2.2 | 安装依赖 | cytoscape, axios, vue-router@4 |
| 1.2.3 | 配置 Vite 代理 | `vite.config.js` proxy → `http://localhost:8000` |
| 1.2.4 | 创建路由配置 | `frontend/src/router/index.js`（6 个 Tab 路由） |
| 1.2.5 | 创建 `App.vue` | Tab 导航栏布局（1920×1080 满屏） |
| 1.2.6 | 创建 6 个空视图组件 | `KnowledgeGraphView.vue`, `RAGQueryView.vue`, `KnowledgeMergeView.vue`, `AgentView.vue`, `ReportView.vue`, `SettingsView.vue` |
| 1.2.7 | 创建 API 客户端 | `frontend/src/api/client.js`（axios 实例） |
| 1.2.8 | 创建全局样式 | `frontend/src/styles/main.css`（reset + 主题变量）|

### Plan 1.3 — 基础设施

| 步骤 | 操作 | 文件 |
|------|------|------|
| 1.3.1 | 创建 `package.json`（根目录） | 含 `docker-compose` 相关 script |
| 1.3.2 | 创建 `docker-compose.yml` | 后端服务 + 前端服务 |
| 1.3.3 | 创建 `Dockerfile`（backend） | Python 3.11 slim 镜像 |
| 1.3.4 | 验证：`uvicorn src.main:app` 启动成功 | 访问 `http://localhost:8000/docs` |

**完成标志:** 前后端均能启动，API 文档可访问，前端 Tab 导航渲染正常

---

## Task 2: 数据解析模块（Ingestion Pipeline）

**前提 Task:** Task 1

**目标:** 实现 5 种格式解析器，输出标准化 JSON Schema，提供上传 API

### Plan 2.1 — 解析数据结构定义

| 步骤 | 操作 | 文件 |
|------|------|------|
| 2.1.1 | 定义 Pydantic Model | `src/ingestion/models.py` |
| | | → `TextbookSchema`（textbook_id, filename, title, total_pages, total_chars, chapters[]）|
| | | → `ChapterSchema`（chapter_id, title, page_start, page_end, content, char_count）|
| 2.1.2 | 定义解析器抽象基类 | `src/ingestion/__init__.py` → `BaseParser(ABC)` |

### Plan 2.2 — PDF 解析器

| 步骤 | 操作 | 文件 |
|------|------|------|
| 2.2.1 | PyMuPDF 打开文档、提取目录 | `src/ingestion/pdf_parser.py` → `PDFParser` |
| 2.2.2 | 按 TOC 结构分割章节 | 无 TOC 时按页码切分 |
| 2.2.3 | 逐页提取纯文本，计算 char_count | |
| 2.2.4 | 组装 `TextbookSchema` 并返回 | |

### Plan 2.3 — Markdown / TXT / DOCX / Excel 解析器

| 步骤 | 操作 | 文件 |
|------|------|------|
| 2.3.1 | Markdown 解析器 | `src/ingestion/md_parser.py` — 按 `#/##/###` 分割 |
| 2.3.2 | TXT 解析器 | `src/ingestion/txt_parser.py` — 按空行/分隔符分割 |
| 2.3.3 | DOCX 解析器 | `src/ingestion/docx_parser.py` — 按 Heading 样式分割 |
| 2.3.4 | Excel 解析器 | `src/ingestion/excel_parser.py` — Sheet 作章节，行作内容 |
| 2.3.5 | 解析器工厂 | `src/ingestion/parser_factory.py` → 根据扩展名分发 |

### Plan 2.4 — 解析 API 与存储

| 步骤 | 操作 | 文件 |
|------|------|------|
| 2.4.1 | POST `/api/ingestion/upload` | `src/api/ingestion_routes.py` |
| | | multipart 上传 → 识别格式 → 解析 → 存 JSON 到 `data/parsed/` |
| 2.4.2 | GET `/api/ingestion/list` | 返回已解析教科书列表 |
| 2.4.3 | DELETE `/api/ingestion/{textbook_id}` | 删除解析数据 |

**完成标志:** 上传 PDF/MD/TXT/DOCX/Excel 文件均可正确解析，API 返回完整 JSON Schema

---

## Task 3: 知识图谱构建与合并

**前提 Task:** Task 2

**目标:** LLM 驱动从教科书内容提取知识节点和关系，实现跨书合并

### Plan 3.1 — 节点抽取

| 步骤 | 操作 | 文件 |
|------|------|------|
| 3.1.1 | 实现 LLM API 调用封装 | `src/knowledge_graph/builder.py` |
| 3.1.2 | 设计节点抽取 few-shot prompt | 含 category 分类体系 |
| 3.1.3 | 逐章调用 LLM 抽取节点 | 分批处理大文本，避免超长 context |
| 3.1.4 | 解析 LLM 输出 JSON | 异常重试 + schema 校验 |

### Plan 3.2 — 关系抽取

| 步骤 | 操作 | 文件 |
|------|------|------|
| 3.2.1 | 设计关系抽取 prompt | `src/knowledge_graph/relation_extractor.py` |
| | | 四种关系：prerequisite / parallel / contains / applies_to |
| 3.2.2 | 实现节点对批量关系判断 | 按章节内节点对组合 |
| 3.2.3 | 添加 few-shot 示例 | 每类关系 1-2 个示例 |

### Plan 3.3 — 图谱存储

| 步骤 | 操作 | 文件 |
|------|------|------|
| 3.3.1 | NetworkX 图构建 | `src/knowledge_graph/graph_store.py` |
| 3.3.2 | 导出 `nodes.json` / `edges.json` | 持久化到 `data/knowledge_graph/` |
| 3.3.3 | 图序列化/反序列化 | 支持重启加载 |

### Plan 3.4 — 知识合并

| 步骤 | 操作 | 文件 |
|------|------|------|
| 3.4.1 | Embedding 相似度初筛 | `src/knowledge_graph/merger.py` |
| 3.4.2 | 候选组 LLM 合并决策 | merge / keep / remove + confidence |
| 3.4.3 | 合并执行（合并属性和引用） | 更新 graph_store |
| 3.4.4 | POST `/api/graph/merge` API | 触发合并流程 |
| 3.4.5 | GET `/api/graph/merge/status` | 合并进度 + 去重率统计 |

### Plan 3.5 — 图谱 API

| 步骤 | 操作 | 文件 |
|------|------|------|
| 3.5.1 | GET `/api/graph/nodes` | 支持 textbook_id 筛选 | `src/api/graph_routes.py` |
| 3.5.2 | GET `/api/graph/edges` | 支持 relation_type 筛选 |
| 3.5.3 | GET `/api/graph/search?q=` | 节点搜索 |

**完成标志:** 上传教科书后可自动构建知识图谱，节点 + 边数据可通过 API 获取，跨书合并去重率 ≥30%

---

## Task 4: 知识图谱可视化与图问答

**前提 Task:** Task 3

**目标:** 前端渲染交互式知识图谱，支持自然语言图查询

### Plan 4.1 — Cytoscape.js 画布组件

| 步骤 | 操作 | 文件 |
|------|------|------|
| 4.1.1 | 封装 `GraphCanvas.vue` | `frontend/src/components/GraphCanvas.vue` |
| | | 接收 nodes/edges props → cytoscape 实例化 |
| 4.1.2 | 配置节点样式 | 按 category 分别着色，显示名称标签 |
| 4.1.3 | 配置边样式 | 按 relation_type 分别着色 + 箭头 |
| 4.1.4 | 力导向布局 | `cose` 布局 + 可切换 `breadthfirst` / `circle` |
| 4.1.5 | 交互: 点击/拖拽/缩放 | 节点点击高亮 + 侧边栏显示详情 |

### Plan 4.2 — 图谱筛选与搜索

| 步骤 | 操作 | 文件 |
|------|------|------|
| 4.2.1 | `GraphFilter.vue` 筛选面板 | 按 category / relation_type 过滤 | `frontend/src/components/GraphFilter.vue` |
| 4.2.2 | 搜索框实现 | 实时模糊匹配节点名称，定位到画布中心 |
| 4.2.3 | 图例组件 | 显示颜色对应的 category 和 relation_type |

### Plan 4.3 — 图问答引擎

| 步骤 | 操作 | 文件 |
|------|------|------|
| 4.3.1 | NL → Graph Query 转换 | `src/knowledge_graph/query_engine.py` |
| | | LLM 解析自然语言到图操作（neighbors / path / subgraph） |
| 4.3.2 | 图遍历执行 | BFS/DFS 深度限定 2-3 层 |
| 4.3.3 | LLM 解释结果 | 将子图转为自然语言回答 |
| 4.3.4 | POST `/api/graph/query` | 接受自然语言，返回子图 + 解释 |

### Plan 4.4 — 知识图谱 Tab 页面集成

| 步骤 | 操作 | 文件 |
|------|------|------|
| 4.4.1 | 组装 `KnowledgeGraphView.vue` | 左侧画布 + 右侧详情/查询侧边栏 | `frontend/src/views/KnowledgeGraphView.vue` |
| 4.4.2 | 数据流对接 | 从 API 加载 nodes/edges → 传入 GraphCanvas |
| 4.4.3 | 查询面板集成 | 输入框 → POST `/api/graph/query` → 高亮结果 |

**完成标志:** 知识图谱以交互式图形渲染，支持筛选/搜索/点击查看详情，自然语言图查询可用

---

## Task 5: RAG Pipeline 构建

**前提 Task:** Task 2

**目标:** 完整 RAG pipeline（分块→嵌入→检索→生成）+ 混合检索 + API

### Plan 5.1 — Chunk 策略实现

| 步骤 | 操作 | 文件 |
|------|------|------|
| 5.1.1 | 实现递归分块器 | `src/rag/chunker.py` |
| | | 按章节→段落→句子逐级回退 |
| 5.1.2 | 目标长度 500-800 chars | overlap 50-100 chars |
| 5.1.3 | Chunk metadata 标注 | 绑定 textbook_id, chapter_id, page, char_offset |

### Plan 5.2 — Embedding 引擎

| 步骤 | 操作 | 文件 |
|------|------|------|
| 5.2.1 | 封装 Embedder（支持多后端） | `src/rag/embedder.py` |
| | | sentence-transformers / OpenAI Embedding API 可切换 |
| 5.2.2 | 默认模型加载 | paraphrase-multilingual-MiniLM-L12-v2（384 维） |
| 5.2.3 | 批量 embedding 编码 | 支持进度回调 |

### Plan 5.3 — 向量存储与混合检索

| 步骤 | 操作 | 文件 |
|------|------|------|
| 5.3.1 | FAISS 索引构建 | `src/rag/vector_store.py` |
| | | IndexFlatIP（内积）或 IndexIVFFlat（大规模） |
| 5.3.2 | BM25 索引构建 | 使用 rank_bm25 库 |
| 5.3.3 | 混合检索器 | `src/rag/retriever.py` |
| | | FAISS top-10 + BM25 top-10 → RRF 融合 → top-5 |
| 5.3.4 | 索引持久化 | 保存到 `data/chunks/` |

### Plan 5.4 — LLM 生成器

| 步骤 | 操作 | 文件 |
|------|------|------|
| 5.4.1 | 设计回答生成 prompt | `src/rag/generator.py` |
| | | 含 context 注入 + 引用格式要求 |
| 5.4.2 | 引用抽取 | 从 LLM 输出解析 [来源：...] 标记 |
| 5.4.3 | 结构化响应组装 | answer + citations[] + source_chunks[] |

### Plan 5.5 — RAG API

| 步骤 | 操作 | 文件 |
|------|------|------|
| 5.5.1 | POST `/api/rag/index` | 对指定 textbook_id 执行索引 | `src/api/rag_routes.py` |
| 5.5.2 | POST `/api/rag/query` | 混合检索 + 生成 |
| 5.5.3 | GET `/api/rag/status` | 查询索引状态 |

**完成标志:** 上传教材后可索引，RAG 问答返回带引用的正确答案

---

## Task 6: Agent 系统

**前提 Task:** Task 5

**目标:** 多 Agent 协作工作流，支持问题分解→规划→检索→综合

### Plan 6.1 — Agent 基类与 Prompt 管理

| 步骤 | 操作 | 文件 |
|------|------|------|
| 6.1.1 | 定义 `BaseAgent` 抽象类 | `src/agent/__init__.py` |
| | | `run(input) → output` 统一接口 |
| 6.1.2 | Prompt 模板管理 | YAML 或 JSON 集中管理所有 Agent prompt |

### Plan 6.2 — Decomposer Agent

| 步骤 | 操作 | 文件 |
|------|------|------|
| 6.2.1 | 实现问题分解 prompt | `src/agent/agent_decomposer.py` |
| | | 复杂问题 → 3-5 个原子子问题 |
| 6.2.2 | 输出解析 | 子问题列表 + 依赖关系 |

### Plan 6.3 — Planner Agent

| 步骤 | 操作 | 文件 |
|------|------|------|
| 6.3.1 | 实现规划 prompt | `src/agent/agent_planner.py` |
| | | 为子问题分配执行顺序和检索资源（RAG / KG）|

### Plan 6.4 — Searcher Agent & KG Agent

| 步骤 | 操作 | 文件 |
|------|------|------|
| 6.4.1 | Searcher Agent | `src/agent/agent_retriever.py` |
| | | 调用 RAG pipeline 检索信息 |
| 6.4.2 | KG Agent | 调用知识图谱 query_engine |

### Plan 6.5 — Synthesizer Agent

| 步骤 | 操作 | 文件 |
|------|------|------|
| 6.5.1 | 综合 prompt 设计 | `src/agent/agent_synthesizer.py` |
| | | 融合所有 Agent 输出 → 连贯回答 |
| 6.5.2 | 引用溯源 | 保留每个论断的原始引用信息 |

### Plan 6.6 — Orchestrator 与工作流定义

| 步骤 | 操作 | 文件 |
|------|------|------|
| 6.6.1 | 实现 Orchestrator | `src/agent/orchestrator.py` |
| | | 按依赖图执行 Agent，支持并行 |
| 6.6.2 | 工作流状态管理 | Agent 执行过程可追踪 |
| 6.6.3 | Mermaid 工作流图生成 | `src/agent/agent_workflow.py` |
| | | 动态生成流程图的 Mermaid 字符串 |
| 6.6.4 | POST `/api/agent/query` | 触发 Agent 工作流 |

**完成标志:** Agent 接收问题后自动分解、规划、检索、综合，返回含多来源引用的回答

---

## Task 7: UI 完整整合与交互完善

**前提 Task:** Task 4, Task 6

**目标:** 所有功能的前端 UI 完整实现，交互流畅

### Plan 7.1 — RAG 问答 Tab

| 步骤 | 操作 | 文件 |
|------|------|------|
| 7.1.1 | 实现 `ChatPanel.vue` 通用组件 | 消息列表 + Markdown 渲染 | `frontend/src/components/ChatPanel.vue` |
| 7.1.2 | 实现 `CitationCard.vue` | 引用来源卡片显示 | `frontend/src/components/CitationCard.vue` |
| 7.1.3 | 组装 `RAGQueryView.vue` | 对话记录 + 引用卡片区域 | `frontend/src/views/RAGQueryView.vue` |

### Plan 7.2 — Agent Tab

| 步骤 | 操作 | 文件 |
|------|------|------|
| 7.2.1 | Mermaid 工作流图渲染 | 使用 mermaid.js 库解析流程图字符串 | `frontend/src/views/AgentView.vue` |
| 7.2.2 | Agent 对话面板 | 展示 Agent 思考过程（可展开/折叠） |
| 7.2.3 | 实时流式输出 | Server-Sent Events 展示 Agent 执行进度 |

### Plan 7.3 — 知识合并 Tab

| 步骤 | 操作 | 文件 |
|------|------|------|
| 7.3.1 | 合并概览面板 | 去重率统计、待处理合并候选列表 | `frontend/src/views/KnowledgeMergeView.vue` |
| 7.3.2 | 合并决策交互 | 展示 LLM 建议（merge/keep/remove），人工确认 |
| 7.3.3 | 合并前后对比 | 图谱变化 diff 展示 |

### Plan 7.4 — 上传与设置 Tab

| 步骤 | 操作 | 文件 |
|------|------|------|
| 7.4.1 | 实现 `UploadZone.vue` | 拖拽/点击上传 + 进度条 | `frontend/src/components/UploadZone.vue` |
| 7.4.2 | Settings Tab | LLM 配置、Embedding 模型选择、服务器地址 | `frontend/src/views/SettingsView.vue` |
| 7.4.3 | 报告 Tab 骨架 | 显示 Markdown 报告 | `frontend/src/views/ReportView.vue` |

### Plan 7.5 — 全局 UI 打磨

| 步骤 | 操作 | 文件 |
|------|------|------|
| 7.5.1 | 状态栏 | 实时显示索引教材数、节点数、去重率 |
| 7.5.2 | 错误处理 | 全局错误弹窗 + 网络重连提示 |
| 7.5.3 | 加载状态 | 骨架屏 / loading spinner |
| 7.5.4 | 响应式适配 | 确保 1920×1080 完美显示 |

**完成标志:** 所有 Tab 功能完整可用，交互反馈流畅，无功能性缺失

---

## Task 8: 文档、报告、Docker 与 Benchmark

**前提 Task:** Task 7

**目标:** 完善所有文档、生成竞赛报告、容器化部署、RAG Benchmark

### Plan 8.1 — API 文档

| 步骤 | 操作 | 文件 |
|------|------|------|
| 8.1.1 | 编写 `docs/api.md` | 所有 API 端点 + 请求/响应示例 | `docs/api.md` |
| | | 含认证说明、错误码表 |
| 8.1.2 | FastAPI 自动生成文档确认 | 确保 `/docs` 页面完整 |

### Plan 8.2 — 系统设计文档

| 步骤 | 操作 | 文件 |
|------|------|------|
| 8.2.1 | 编写 `docs/design.md` | `docs/design.md` |
| | | 架构图（C4 模型）、模块说明、数据流图 |
| 8.2.2 | 组件交互说明 | 后端模块间调用关系 |

### Plan 8.3 — Agent 文档

| 步骤 | 操作 | 文件 |
|------|------|------|
| 8.3.1 | 编写 `docs/Agent.md` | `docs/Agent.md` |
| | | 每个 Agent 的 prompt 设计、工作流 Mermaid 图 |
| 8.3.2 | Agent 决策逻辑说明 | 错误恢复、超时处理、重试策略 |

### Plan 8.4 — 竞赛报告

| 步骤 | 操作 | 文件 |
|------|------|------|
| 8.4.1 | 实现报告生成器 | `src/report/generator.py` |
| 8.4.2 | 生成完整 7 项报告 | `report/competition_report.md` |
| | | Abstract / Problem / Approach / Experiments / Limitations / References |

### Plan 8.5 — RAG Benchmark

| 步骤 | 操作 | 文件 |
|------|------|------|
| 8.5.1 | 构建 ground truth Q&A 集 | `src/rag/benchmark.py` |
| 8.5.2 | Chunk size 对比实验 | 200 / 500 / 800 / 1200 |
| 8.5.3 | 检索策略对比 | 纯向量 vs 混合 BM25 |
| 8.5.4 | Token 消耗统计 | 各策略开销报告 |
| 8.5.5 | Benchmark 报告 | 嵌入到竞赛报告 Experiments 章节 |

### Plan 8.6 — Docker 部署

| 步骤 | 操作 | 文件 |
|------|------|------|
| 8.6.1 | 完善 `Dockerfile` | 多阶段构建（frontend build + backend） |
| 8.6.2 | 完善 `docker-compose.yml` | backend + frontend（可选 chromadb/redis） |
| 8.6.3 | docker-compose 一键启动验证 | 确保全功能可用 |

### Plan 8.7 — README 完善

| 步骤 | 操作 | 文件 |
|------|------|------|
| 8.7.1 | 项目介绍 + 功能列表 | `README.md` |
| 8.7.2 | 环境要求 + 安装步骤 | pip install / npm install 命令 |
| 8.7.3 | 环境变量配置说明 | .env 模板 |
| 8.7.4 | 快速开始 + 使用示例 | 从启动到完成一次问答的完整流程 |
| 8.7.5 | Docker 部署指引 | docker-compose up 命令 |

**完成标志:** 文档完整可读、竞赛报告覆盖所有评分项、`docker-compose up` 一键启动、Benchmark 数据可复现

---

## 附录: Task 里程碑总览

| Task | 名称 | 依赖 | 预估工时 | 核心产出物 |
|------|------|------|---------|-----------|
| 1 | 项目骨架 | 无 | 2 天 | FastAPI+Vue3 项目、docker-compose |
| 2 | 数据解析 | Task 1 | 3 天 | 5 解析器 + API + JSON Schema |
| 3 | 图谱构建 | Task 2 | 4 天 | 节点/关系抽取、合并、API |
| 4 | 图谱可视化 | Task 3 | 3 天 | Cytoscape.js 画布、图问答 |
| 5 | RAG Pipeline | Task 2 | 4 天 | 分块→嵌入→混合检索→生成 |
| 6 | Agent 系统 | Task 5 | 4 天 | 5 Agent + Orchestrator + API |
| 7 | UI 整合 | Task 4, 6 | 4 天 | 全部 Tab 就绪、交互打磨 |
| 8 | 文档/报告/Docker | Task 7 | 3 天 | 4 文档 + 报告 + Benchmark + Docker |
| | **合计** | | **27 天** | |
