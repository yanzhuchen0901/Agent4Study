# Agent4Study

Agent4Study 是一个 AI 教科书知识系统，用于多教材解析、知识图谱构建、跨教材整合、RAG 问答、Agent 工作流展示和竞赛报告预览。

## 功能

- 教材解析：支持 PDF、Markdown、TXT、DOCX、Excel。
- 知识图谱：节点/关系抽取、Cytoscape 可视化、自然语言图查询。
- 知识合并：跨教材候选合并、LLM 建议、人工确认。
- RAG：混合向量 + BM25 检索、引用来源、原文片段。
- Agent：多 Agent 编排，支持 SSE 实时执行轨迹。
- 报告：Markdown 竞赛报告预览和可复现 Benchmark。

## 环境要求

- Python 3.11+
- Node.js 20+
- npm 10+
- Docker Desktop（可选）

## 环境变量

复制 `.env.example` 为 `.env`，至少配置：

```env
LLM_PROVIDER=deepseek
LLM_MODEL=deep-seek-v4-flash
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.deepseek.com
```

不要提交 `.env`、教材 PDF、解析产物或本地索引。

## 本地启动

安装依赖：

```bash
pip install -r requirements.txt
npm install
npm --prefix frontend install
```

启动后端：

```bash
npm run dev:backend
```

启动前端：

```bash
npm run dev:frontend
```

访问：

- 前端：http://localhost:5173
- 后端健康检查：http://localhost:8000/health
- FastAPI 文档：http://localhost:8000/docs

## 使用流程

1. 进入“设置”上传教材文件。
2. 进入“知识图谱”输入 `textbook_id` 构建图谱。
3. 进入“RAG 问答”建立索引并提问。
4. 进入“知识合并”生成候选并人工确认。
5. 进入“Agent”提出复杂问题，查看实时工作流。
6. 进入“报告”查看竞赛报告 Markdown。

## Benchmark 与报告

运行 RAG Benchmark：

```bash
python -m src.rag.benchmark
```

生成竞赛报告：

```bash
python -m src.report.generator
```

输出：

- `data/rag_benchmark/benchmark_report.json`
- `report/competition_report.md`
- `report/整合报告.md`
- `docs/report.md`

## Docker

一键启动：

```bash
docker compose up --build
```

访问：

- 前端：http://localhost:5173
- 后端：http://localhost:8000

Docker Compose 会挂载本地 `data/` 和 `report/`，便于保留教材解析、索引、图谱和报告结果。

## 文档

- `docs/api.md`：API 端点和请求/响应说明。
- `docs/design.md`：架构、模块和数据流。
- `docs/Agent.md`：Agent 设计、工作流和错误恢复。
- `docs/report.md`：竞赛报告副本。
