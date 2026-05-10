# Agent4Study 代码仓库分析与改进参考

> 基于 `C:\Users\a1921\Desktop\Agent4Study` 代码仓库分析  
> 文件路径双向引用: `Agent4Study/` 下所有源代码

---

## 一、项目全景评估

### 已实现功能（当前状态良好）

| 模块 | 文件引用 | 状态 |
|------|---------|------|
| 教材解析 (5格式) | `src/ingestion/pdf_parser.py`, `md_parser.py`, `txt_parser.py`, `docx_parser.py`, `excel_parser.py` + `parser_factory.py` | **完成** |
| 知识图谱构建 | `src/knowledge_graph/builder.py`, `relation_extractor.py`, `graph_store.py` | **完成** |
| 知识图谱可视化 | `frontend/src/components/GraphCanvas.vue` (Cytoscape.js) + `GraphFilter.vue` | **完成** |
| 知识图谱问答 | `src/knowledge_graph/query_engine.py` + `KnowledgeGraphView.vue` | **完成** |
| 知识合并 | `src/knowledge_graph/merger.py` + `KnowledgeMergeView.vue` (含人工确认) | **完成** |
| RAG Pipeline | `src/rag/chunker.py`, `retriever.py`, `generator.py`, `vector_store.py` | **完成** |
| RAG 前端 | `RAGQueryView.vue` + `ChatPanel.vue` + `CitationCard.vue` | **完成** |
| Agent 工作流 | `src/agent/orchestrator.py`, `agent_decomposer.py`, `agent_synthesizer.py` + `AgentView.vue` (SSE) | **完成** |
| 报告预览 | `src/api/report_routes.py` + `ReportView.vue` | **完成** |
| 设置/上传 | `SettingsView.vue` + `UploadZone.vue` + `src/api/settings_routes.py` | **完成** |
| Docker | `Dockerfile` + `docker-compose.yml` | **完成** |
| 文档 | `README.md`, `docs/api.md`, `docs/design.md`, `docs/Agent.md`, `docs/report.md` | **完成** |

### 数据状态

| 文件 | 引用 | 状态 |
|------|------|------|
| `data/knowledge_graph/nodes.json` | GraphStore 读写 | **空数组 `[]`** |
| `data/knowledge_graph/edges.json` | GraphStore 读写 | **空数组 `[]`** |
| `data/rag_benchmark/benchmark_report.json` | RAGBenchmark 输出 | 待检查 |

---

## 二、必须修复的关键问题

### 🔴 P0: LLM 配置传递方式（架构级问题）

**现状**: `src/knowledge_graph/llm_client.py` 直接读 `get_settings()` 的 `llm_api_key` 和 `llm_model`（`src/config.py` 行 48-49），只能通过 `.env` 文件配置，前端 Settings 页无法设置 LLM 参数。

**影响**: 
- 用户换模型必须改 `.env` + 重启后端
- 无法支持"前端自由切换 DeepSeek/OpenAI/硅基流动"

**修改方案**:

<file:src/knowledge_graph/llm_client.py>
```python
# 当前：硬读 settings
class GraphLLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        client = OpenAI(
            api_key=self.settings.llm_api_key,  # ← 直接从 .env 读
            base_url=self.settings.llm_base_url,
        )

# 改为：支持从参数传入 llm_config
class GraphLLMClient:
    def __init__(self, llm_config: dict | None = None) -> None:
        self.settings = get_settings()
        self.llm_config = llm_config or {}  # 前端传入 {api_key, base_url, model}
    
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        api_key = self.llm_config.get("api_key") or self.settings.llm_api_key
        base_url = self.llm_config.get("base_url") or self.settings.llm_base_url
        model = self.llm_config.get("model") or self.settings.llm_model
        client = OpenAI(api_key=api_key, base_url=base_url)
```

**涉及的所有 API 路由** 都需要添加 `llm_config` 参数:
- `src/api/graph_routes.py` → `POST /api/graph/build`, `POST /api/graph/query`
- `src/api/rag_routes.py` → `POST /api/rag/query`
- `src/api/agent_routes.py` → `POST /api/agent/query`

**前端 Settings 页 (`frontend/src/views/SettingsView.vue`)** 需要新增 LLM 配置表单:
- Base URL 输入框
- API Key 输入框（`type="password"`）
- Model 名输入框
- 保存到 `localStorage`

**前端 API 调用 (`frontend/src/api/client.js`)** 每次请求从 localStorage 读配置并附加:

```javascript
function getLLMConfig() {
  return {
    api_key: localStorage.getItem('a4s.llmApiKey') || '',
    base_url: localStorage.getItem('a4s.llmBaseUrl') || 'https://api.deepseek.com',
    model: localStorage.getItem('a4s.llmModel') || '',
  }
}
```

### 🔴 P1: Embedding 实现是 Hash 占位符（功能正确性）

**现状**: `src/rag/embedder.py` 行 20-31 使用 `_hash_embed`（MD5 哈希映射），**不是真正的语义嵌入**。虽然 `requirements.txt` 列出了 `sentence-transformers`，但未被使用。

```python
def _hash_embed(self, text: str) -> np.ndarray:
    # 这是占位实现！MD5 哈希不包含语义信息
    vector = np.zeros(self.dimension, dtype="float32")
    tokens = self._tokens(text)
    for token in tokens:
        digest = hashlib.md5(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "little") % self.dimension
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(float(np.dot(vector, vector)))
    if norm > 0:
        vector /= norm
    return vector
```

**影响**: 
- 语义搜索功能退化，检索结果基于随机的 token 哈希碰撞
- RAG 回答质量不可靠，因为检索到的 chunks 语义不相关
- Hybrid 检索实际只有 BM25 在起作用

**修改方案**: 替换为真实 sentence-transformers 调用：

<file:src/rag/embedder.py>
```python
class Embedder:
    def __init__(self, dimension: int = 384) -> None:
        self.settings = get_settings()
        self.dimension = dimension
        self._model = None  # 延迟加载
    
    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(
                    self.settings.embedding_model,
                    device='cpu'
                )
            except ImportError:
                raise RuntimeError("sentence-transformers not installed")
        return self._model
    
    def encode(self, texts: list[str]) -> np.ndarray:
        model = self._get_model()
        return model.encode(texts, normalize_embeddings=True).astype("float32")
```

---

## 三、重要优化建议

### 🟡 P2: CORS 配置写死

<file:src/main.py>
```python
# 当前只允许 5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
)

# 改为允许所有 Vite 端口或从环境变量读取
import os
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS.split(",")],
)
```

### 🟡 P2: GraphStore 未充分发挥 NetworkX 能力

<file:src/knowledge_graph/merger.py>
- 当前合并使用 `SequenceMatcher` 做相似度匹配，没有用 `node_by_id` 和图算法
- 建议后续合并时利用 NetworkX 的子图同构、连通分量等算法增强去重

### 🟡 P2: Decomposer Agent 未调用 LLM

<file:src/agent/agent_decomposer.py>
- 当前仅用正则 `re.split` 做简单字符串分割
- 建议改为调用 LLM 做语义分解，或至少保留当前正则 + 添加 LLM 选项

### 🟡 P2: Planner Agent 策略过于简单

<file:src/agent/agent_planner.py>
- 对所有子问题都生成 RAG + KG 两步，无法动态规划
- 后续优化：让 LLM 决定每个子问题走 RAG 还是 KG 还是两者

### 🟡 P2: 前端缺少 LLM API Key 配置 UI

<file:frontend/src/views/SettingsView.vue>
- `preferences` 中有 `apiBase`, `defaultTopK`, `graphLayout`, `enableSse`
- **缺少**: `llmApiKey`, `llmBaseUrl`, `llmModel` 三个字段

---

## 四、边缘情况与代码健壮性

### ⚠️ P3: 知识合并空图谱处理

<file:src/knowledge_graph/merger.py>
- `merge_cross_books()` 在 `nodes` 为空时 `_candidate_groups` 返回 `[]`，行为正确
- 但 `_apply_merge` 中 `group[0].model_copy(deep=True)` 在 group 为空时会 IndexError

### ⚠️ P3: RAG 检索无索引时优雅降级

<file:src/rag/retriever.py>
```python
def retrieve(self, query: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
    chunks = self.store.load_chunks()
    embeddings = self.store.load_embeddings()
    if not chunks or embeddings.size == 0:
        return []  # ✅ 已正确处理
```

### ⚠️ P3: Agent Orchestrator 未传递 LLM config

<file:src/agent/orchestrator.py>
- Searcher 和 KG Agent 内部各自 `HybridRetriever()` 和 `GraphQueryEngine()`，没有 llm_config 透传机制

---

## 五、与设计文档（`-ref`）的差异

| 设计文档要求 | 当前实现 | 差异 |
|------------|---------|------|
| Embedding: sentence-transformers | MD5 hash | **待修复** |
| FAISS 向量索引 | numpy 文件 (.npy) | 功能可工作但非 FAISS |
| Agent 用 LLM 分解问题 | 正则分割 | 简化实现 |
| Settings API 读写 | 只读 (.env) | 设计是 localStorage 但后端硬依赖 env |
| 报告 Generator | 同时存在报告路由和 generator.py | 功能重叠 |

---

## 六、修改优先级建议

| 优先级 | 项目 | 涉及文件数 | 预估工时 |
|--------|------|-----------|---------|
| **P0** | LLM 配置从前端传递 | ~10 文件 | 2-3h |
| **P1** | Embedding 替换为真实模型 | 2 文件 | 1h |
| **P2** | CORS 允许更多端口 | 1 文件 | 5min |
| **P2** | 前端 LLM 配置 UI | 2 文件 | 1h |
| **P3** | 边缘异常处理 | 3 文件 | 30min |

---

## 七、文件清单速查

```
后端核心 (Python/FastAPI):
├── src/main.py                          # FastAPI 入口 + CORS
├── src/config.py                        # 环境变量配置
├── src/ingestion/
│   ├── models.py                        # TextbookSchema, ChapterSchema
│   ├── pdf_parser.py                    # PyMuPDF 解析
│   ├── md_parser.py                     # Markdown 解析
│   ├── txt_parser.py                    # TXT 解析
│   ├── docx_parser.py                   # DOCX 解析
│   ├── excel_parser.py                  # Excel 解析
│   ├── parser_factory.py                # 工厂模式分发
│   └── utils.py                         # 公共工具
├── src/knowledge_graph/
│   ├── models.py                        # KnowledgeNode, KnowledgeEdge, MergeDecision
│   ├── llm_client.py                    # LLM API 调用封装 ★ 需修改
│   ├── builder.py                       # 节点抽取
│   ├── relation_extractor.py            # 关系抽取
│   ├── graph_store.py                   # NetworkX 存储
│   ├── merger.py                        # 跨书合并
│   └── query_engine.py                  # 图问答
├── src/rag/
│   ├── models.py                        # Chunk, Citation, RAGQueryResult
│   ├── chunker.py                       # 递归分块
│   ├── embedder.py                      # ★ Hash占位, 需替换
│   ├── vector_store.py                  # 向量/块存储
│   ├── retriever.py                     # Hybrid 检索
│   ├── generator.py                     # LLM 生成
│   └── benchmark.py                     # Benchmark 评测
├── src/agent/
│   ├── __init__.py                      # BaseAgent, AgentStep, AgentResult
│   ├── agent_decomposer.py              # ★ 未用LLM
│   ├── agent_planner.py                 # ★ 策略简化
│   ├── agent_retriever.py               # Searcher + KG Agent
│   ├── agent_synthesizer.py             # 综合回答
│   ├── agent_workflow.py                # Mermaid 生成
│   └── orchestrator.py                  # Agent 编排
├── src/api/
│   ├── agent_routes.py                  # POST /api/agent/query (+ SSE)
│   ├── graph_routes.py                  # POST /api/graph/{build,query,merge}
│   ├── ingestion_routes.py              # POST /api/ingestion/upload
│   ├── rag_routes.py                    # POST /api/rag/{index,query}
│   ├── report_routes.py                 # GET /api/report/markdown
│   └── settings_routes.py               # GET /api/settings

前端 (Vue 3 + Vite):
├── frontend/src/
│   ├── App.vue                          # 主布局 + Tab 导航
│   ├── router/index.js                  # 6 路由
│   ├── api/client.js                    # ★ 需加 llm_config 参数
│   ├── styles/main.css                  # 全局样式
│   ├── views/
│   │   ├── KnowledgeGraphView.vue       # 图谱交互
│   │   ├── RAGQueryView.vue             # RAG 问答
│   │   ├── KnowledgeMergeView.vue       # 知识合并
│   │   ├── AgentView.vue                # Agent 工作流
│   │   ├── ReportView.vue               # 报告预览
│   │   └── SettingsView.vue             # ★ 需加 LLM 配置
│   └── components/
│       ├── GraphCanvas.vue              # Cytoscape.js 画布
│       ├── GraphFilter.vue              # 筛选面板
│       ├── ChatPanel.vue                # 对话面板
│       ├── CitationCard.vue             # 引用卡片
│       └── UploadZone.vue               # 上传区域（占位）
```

---

## 八、结合 `ref.pdf` 评审报告的基础把握

> `C:\Users\a1921\Desktop\ref.pdf` 是扫描版 AI 评审建议报告，直接文本抽取为空；已按页面图像读取。评审当前给分约 **73/100**，结论不是“系统没做完”，而是“功能基本齐，但评审可见证据不足”。

### 8.1 当前最大矛盾：功能存在，但证据不足

当前仓库已经完成主流程：解析、图谱、RAG、Agent、UI、Docker、报告、Benchmark 框架都有。但评审打分会优先看 README、docs、report 和可跑 demo 数据。如果这些地方仍是占位、空指标或英文/中文文件不一致，就会被误判为未完成。

**核心判断**：

- 代码主干完成度高，继续大改架构 ROI 不高。
- 短期最应补的是“评审可见内容”：中文文档、真实 demo 数据、报告指标、prompt 示例、设计取舍说明。
- 只有少数代码问题属于真正功能正确性风险：Embedding hash 占位、后端 RAG 多轮未接 history、健康检查仍显示 placeholder。

### 8.2 评审点名的高优先级问题

| 问题 | 当前表现 | 风险 | 建议 |
|------|----------|------|------|
| 中文占位文档 | `docs/需求分析.md`、`docs/系统设计.md`、`docs/Agent 架构说明.md`、`docs/接口文档.md` 仍有“待补充” | 评审可能优先点中文文件，误判文档不完整 | 把 `docs/design.md`、`docs/api.md`、`docs/Agent.md` 的实质内容同步/改写到中文文件 |
| 报告指标为空 | `report/competition_report.md` 和 `整合报告.md` 当前 RAG chunks、节点、边、合并决策多为 0 | 报告分低，难证明系统跑通过 | 放 1-2 个小教材样例，跑 upload → graph → rag → merge → benchmark → report |
| Prompt 缺 few-shot | builder/relation_extractor/merger/query_engine/generator 多数是规则化 instruction | Prompt 工程分和 Agent 架构分受影响 | 每类 prompt 加 1 个 few-shot 示例，并在文档写防幻觉策略 |
| Agent 设计取舍不足 | `docs/Agent.md` 有结构，但缺“为什么不用 LangGraph/ReAct/LLM Decomposer” | D 维度设计论证分不足 | 加“设计决策与权衡”章节，说明速度、可控性、依赖体积、调试成本 |
| RAG 策略依据不足 | 有 chunker 和 benchmark，但报告未说明为什么 700/80、RRF 0.7/0.3 | RAG Pipeline 设计分受影响 | 用 benchmark 结果或经验说明写入 `docs/design.md` / `docs/系统设计.md` |
| 可视化进阶不足 | Cytoscape 基础交互完成，但缺 textbook shape、双击展开邻居、合并前后对比 | C 维度进阶分未吃满 | GraphCanvas 加按教材来源 shape，双击节点扩展邻居，高亮子图 |
| 工程成熟度信号不足 | `/health` 仍返回 `stage: task1-scaffold` 和 placeholder 模块状态 | 让评审觉得仍在 Task1 | 更新健康检查 stage/modules 为 task8-complete / ready |

### 8.3 与本文件原 P0/P1 的关系

本文件前面的 **LLM 配置传递** 和 **Embedding 替换真实模型** 是代码正确性问题；`ref.pdf` 指出的主要是评审可见度问题。二者都重要，但如果目标是短时间提分，应先补文档和 demo 报告，再做代码深修。

推荐排序：

1. 先补中文占位文档和报告真实数据，约 1-2 小时，直接影响 A 文档完整性与报告分。
2. 再补 prompt few-shot 和 Agent/RAG 设计取舍，约 1 小时，影响 D 架构与 Prompt 工程分。
3. 然后做可视化进阶，约 30-60 分钟，影响 C 可视化与 F 创新分。
4. 最后做 Embedding / LLM config / RAG history 等功能正确性增强，作为稳定性和演示质量提升。

### 8.4 建议新增的“评审可见交付物”

| 交付物 | 推荐内容 |
|--------|----------|
| `docs/需求分析.md` | 知识点粒度、重复判定标准、教学连贯性、压缩比、RAG 分块依据 |
| `docs/系统设计.md` | 直接承接 `docs/design.md`，补中文架构图、数据流、模块调用关系 |
| `docs/Agent 架构说明.md` | 复制并扩展 `docs/Agent.md`，加入设计决策与权衡、防幻觉策略 |
| `docs/接口文档.md` | 同步 `docs/api.md`，避免中文文件仍是占位 |
| `report/整合报告.md` | 不要与 competition_report 完全相同；顶部加入合并决策摘要、具体 before/after 案例、category 分布 |
| `report/competition_report.md` | 保留 Abstract/Problem/Approach/Experiments/Limits/References，加入真实 benchmark 表 |

### 8.5 Top 5 立即修复建议（按 ROI 排序）

1. **填满 4 个中文占位文档**  
   目标：避免评审优先点中文文档时看到“待补充”。  
   类型：补基础分 + 降误判风险。

2. **跑通 demo 数据并重生成报告**  
   目标：让 `report/整合报告.md` 有节点数、边数、合并决策、RAG chunks、benchmark 结果。  
   类型：补报告分 + 演示可信度。

3. **补 Agent/RAG/Prompt 设计论证**  
   目标：解释为什么选择规则 Decomposer、自研 Orchestrator、RRF 0.7/0.3、chunk 700/80。  
   类型：补架构分。

4. **给 4 类 prompt 各加 few-shot + 防幻觉策略**  
   目标：builder、relation_extractor、merger、query_engine/generator 至少各有一个示例，文档说明 JSON 输出、temperature、失败回退和引用要求。  
   类型：补 Prompt 工程分。

5. **可视化加 textbook shape + 双击展开邻居**  
   目标：在 GraphCanvas 中把 category/color、frequency/size、textbook/shape 三维叠加，并支持双击展开邻居高亮。  
   类型：补可视化进阶分。

---

## 九、对标 `knowledge-integrator-full` 的可采纳改进

> 参考文件：`C:\Users\a1921\Desktop\knowledge-integrator-ref.md`  
> 核心结论：`knowledge-integrator-full` 的优势集中在中文检索、合并聚类、可复现 Mock/Benchmark 和多视图表达；Agent4Study 的优势是 Vue + Cytoscape 交互、分层图谱、SSE Agent 和较完整的前后端工作流。建议只吸收高 ROI 技术点，不做框架迁移。

### 9.1 RAG 检索：优先补中文分词和 Hash 加权

`knowledge-integrator-full` 在 BM25 前使用 Jieba `cut_for_search`，比 Agent4Study 当前 regex 单字切分更适合中文教材。例如“心力衰竭”不应拆成单字，应尽量保留医学/课程术语。

建议：

- 在 `src/rag/vector_store.py` 的 `tokenize()` 中 lazy-load `jieba`。
- `requirements.txt` 增加 `jieba`，若导入失败则回退当前 regex。
- 保持现有 `HybridRetriever` 结构，先不必大改为对方的 Union Pool。
- 若短期不换真实 sentence-transformers，可先把 hash embedding 改成 TF 风格加权：`1 + log(count)`，减少纯 ±1 哈希的随机性。

推荐实现口径：

```python
def tokenize(text: str) -> list[str]:
    jieba = _get_jieba()
    if jieba:
        tokens = [item.strip().lower() for item in jieba.cut_for_search(text)]
        return [item for item in tokens if item and not item.isspace()]
    return re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text.lower())
```

### 9.2 融合策略：RRF 先保留，补充对比说明

`knowledge-integrator-full` 用 Union Pool + min-max 加权融合，Agent4Study 用 RRF：

- Union Pool 优点：利用实际分数，便于调 BM25/vector 权重。
- RRF 优点：对不同检索器分数尺度更鲁棒，工程实现简单。

建议当前不急着替换 RRF。更高 ROI 的做法是：

- 在 `docs/系统设计.md` / `docs/design.md` 说明为什么当前选择 RRF。
- 在 benchmark 中保留 `hybrid-vector-bm25` 与 `bm25-only` 对比。
- 后续若有时间再增加 `fusion_strategy=rrf|minmax` 参数做 A/B，而不是直接重写检索器。

### 9.3 知识节点模型：补 `aliases`、`importance`、`original_text`

对方节点结构比我们更适合“教学整合”评分：

| 字段 | 价值 | 建议优先级 |
|------|------|------------|
| `aliases` | 支持“梯度下降法/最速下降法”等异名合并 | P1 |
| `importance` | 支持压缩比剪枝和教学重点保留 | P1 |
| `original_text` | 让合并/报告能展示原文证据 | P2 |
| `embedding` | 可做节点语义聚类，但会增加存储和迁移成本 | P3 |

建议先在 `KnowledgeNode` 中新增：

```python
aliases: list[str] = Field(default_factory=list)
importance: str = "medium"  # high / medium / low
original_text: str = ""
```

并同步修改：

- `src/knowledge_graph/builder.py`：prompt 要求输出别名、重要性、原文片段。
- `src/knowledge_graph/merger.py`：候选分组时同时看 `name + aliases + definition`。
- `report/整合报告.md`：重点案例能展示 before/after 和原文证据。

### 9.4 知识合并：从 SequenceMatcher 升级到“语义候选 + LLM 择优”

`knowledge-integrator-full` 的合并亮点是 embedding cosine clustering + async LLM 并行 + best version 判断。Agent4Study 当前是 SequenceMatcher + 串行 LLM，只能较好发现名称/定义相近的重复项。

建议分两步吸收：

1. **短期**：保留 SequenceMatcher，但把 `aliases` 纳入候选匹配，并在 LLM prompt 中增加“选择最佳版本”的输出字段。
2. **中期**：引入节点 embedding 聚类，阈值可先用 `0.55-0.70` 区间，通过 demo 数据调参。

推荐合并判断 schema：

```json
{
  "action": "merge|keep|remove",
  "best_node_id": "node_xxx",
  "reason": "为什么相同/不同，以及为什么选择该版本",
  "confidence": 0.0
}
```

注意：当前 Task7 已规定 `remove` 不做破坏性删除。即使引入压缩比剪枝，也应先写入 pending review，由人工确认后再删除或隐藏。

### 9.5 图谱抽取：不急于合并 nodes+edges prompt

`knowledge-integrator-full` 单次 prompt 同时抽 nodes + edges，且 async 并行章节处理；Agent4Study 当前节点和关系分两步抽取。

判断：

- 单 prompt 优点：调用次数少，关系更依赖章节上下文。
- 分步优点：结构更清晰，错误更容易定位，前期实现稳定。

建议保留当前分步架构，只补：

- 每个 prompt 增加 1 个 few-shot。
- 节点抽取增加 `aliases / importance / original_text`。
- 关系抽取增加“若证据不足则不输出关系”的防幻觉约束。
- 后续再考虑按章节并行，而不是立即改成 async 大重构。

### 9.6 Mock LLM 模式：适合演示和评测兜底

`knowledge-integrator-full` 的 Mock 模式很适合比赛演示：无 API Key、网络失败或额度不足时，系统仍可跑完整流程。

建议 Agent4Study 增加：

- `.env.example` 增加 `LLM_MOCK=false`。
- `src/knowledge_graph/llm_client.py` 在 `LLM_MOCK=true` 或缺 key 时返回可预测 JSON。
- Mock 结果要明确标记 `mock: true`，避免报告里误写成真实 LLM 效果。

这项能显著提升 demo 稳定性，但要注意别让评审误以为核心能力只靠 Mock。

### 9.7 可视化：吸收“多视图”思想，但用 Cytoscape 实现

对方有力导向/树状/热力图等多视图；我们已有 Cytoscape 和布局切换。不要迁移到 D3，直接增强现有 `GraphCanvas.vue`：

- category → color
- frequency → node size
- textbook_id → node shape
- relation_type → edge color
- double click → expand neighbors
- merge preview → before/after 两列图谱对比

这能对应 `ref.pdf` 中“多维度可视化”和“合并前后对比”的加分建议。

### 9.8 新的优先级合并表

| 优先级 | 改进项 | 来源 | 预估工时 | 价值 |
|--------|--------|------|----------|------|
| P0 | 填满 4 个中文占位文档 | `ref.pdf` | 1h | 立刻补文档分，降低误判 |
| P0 | 跑 demo 数据并重生成报告 | `ref.pdf` | 1h | 让报告指标不再为 0 |
| P0 | Jieba 中文分词 | `knowledge-integrator` | 30min | 直接提升 BM25 中文检索 |
| P1 | Hash embedding 加 TF 加权或替换 sentence-transformers | 两者共同 | 10-60min | 提升 RAG 检索正确性 |
| P1 | Prompt few-shot + 防幻觉策略 | `ref.pdf` | 45min | 补 Prompt/Agent 架构分 |
| P1 | Node 增加 aliases/importance/original_text | `knowledge-integrator` | 1h | 支持更强合并和报告案例 |
| P2 | 合并 prompt 增加 best_node_id | `knowledge-integrator` | 30min | 提升合并质量和可解释性 |
| P2 | GraphCanvas textbook shape + 双击邻居 | 两者共同 | 45min | 补可视化进阶分 |
| P2 | Mock LLM 模式 | `knowledge-integrator` | 30min | 演示稳定性兜底 |
| P3 | Async LLM 并行和 embedding 聚类 | `knowledge-integrator` | 2-3h | 中期性能/质量增强 |

---

## 十、下一步工作建议

### 短期（1-2 天）
1. **最高 ROI**：补齐 4 个中文占位文档，避免评审误判。
2. **最高 ROI**：准备 1-2 个小教材样例，跑完整 demo 流程并重生成报告。
3. **P0** Jieba 中文分词接入 `tokenize()`，保留 regex fallback。
4. **P1** Embedding 先加 TF 风格 hash 加权；时间允许再切 sentence-transformers。
5. **P1** Prompt few-shot + 防幻觉策略文档。

### 中期（3-5 天）
6. **P0** LLM 配置从前端传递 — 打通"前端设置 Key → API 调用携带"链路。
7. **P1** Node 增加 aliases / importance / original_text。
8. **P2** Agent/RAG 设计取舍说明。
9. **P2** GraphCanvas 增加 textbook shape 和双击展开邻居。
10. **P2** CORS 放宽。
11. **P2** Agent Decomposer 接入 LLM。
12. **P2** 代码边缘情况测试。

### 长期
13. 合并逻辑升级为 embedding 聚类 + async LLM 并行。
14. 增加 Mock LLM 模式用于无 key 演示。
15. 补全单元测试。
16. 多模态（PDF 图片/表格提取）。
17. Ollama 本地模型支持。
