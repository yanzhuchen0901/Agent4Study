# Agent4Study

AI 教科书知识系统，用于多教材解析、知识图谱构建、跨教材整合、RAG 问答和 Agent 工作流展示。

## Current Stage

Task 1: 项目骨架与基础设施。

已完成：

- FastAPI 后端骨架与 `/health`
- Vue 3 + Vite 前端应用外壳
- 6 个功能 Tab 占位页
- 数据、文档、报告和 Docker 基础结构

## Requirements

- Python 3.11+
- Node.js 20+
- npm 10+

## Backend

```bash
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

访问：

- http://localhost:8000/health
- http://localhost:8000/docs

## Frontend

```bash
cd frontend
npm install
npm run dev
```

访问：

- http://localhost:5173

## Docker

```bash
docker compose up --build
```

Task 1 的 Docker 配置用于开发验证，生产部署会在 Task 8 完善。

## Repository Notes

不要提交教材 PDF 或本地密钥。教材文件应通过前端上传进入 `data/textbooks/`，该目录已被 Git 忽略。
