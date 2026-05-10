# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Backend
pip install -r requirements.txt       # Install Python deps
uvicorn src.main:app --reload --port 8000   # Dev server

# Frontend
npm --prefix frontend install         # Install JS deps
npm --prefix frontend run dev         # Dev server (port 5173)
npm --prefix frontend run build       # Production build

# Both (concurrently)
npm run dev:backend                   # = uvicorn src.main:app ...
npm run dev:frontend                  # = npm --prefix frontend run dev
npm run dev                           # Run both via concurrently

# Data pipeline
python -m src.rag.benchmark           # RAG benchmark
python -m src.report.generator        # Generate competition report

# Docker
docker compose up --build             # Single-command full stack

# LLM (use conda on this system)
d:/conda/python.exe -m uvicorn src.main:app --port 8000
```

## Architecture

### Backend (`src/`) — FastAPI

```
src/
├── main.py                    # App entry, CORS, /health
├── config.py                  # Settings from .env
├── ingestion/                 # Textbook parsing (5 formats)
│   ├── parser_factory.py      # Factory dispatch by extension
│   ├── pdf_parser.py          # PyMuPDF
│   ├── md_parser.py / txt_parser.py / docx_parser.py / excel_parser.py
│   ├── models.py              # TextbookSchema, ChapterSchema
│   └── utils.py               # Chapter splitting, text normalization
├── knowledge_graph/           # Knowledge graph engine
│   ├── models.py              # KnowledgeNode, KnowledgeEdge, MergeDecision
│   ├── llm_client.py          # OpenAI-compatible JSON client (temperature=0.1)
│   ├── builder.py             # LLM-driven node extraction
│   ├── relation_extractor.py  # Edge extraction (4 relation types)
│   ├── graph_store.py         # NetworkX + JSON persistence (nodes.json/edges.json)
│   ├── merger.py              # Cross-textbook merge (LLM decisions + human confirm)
│   ├── query_engine.py        # NL → graph query → BFS subgraph
│   └── hierarchy_builder.py   # Auto-generate book/chapter/knowledge three-layer graph
├── rag/                       # Retrieval-Augmented Generation
│   ├── chunker.py             # Recursive 700-char windows, 80-char overlap
│   ├── embedder.py            # SentenceTransformer (hash fallback)
│   ├── vector_store.py        # NumPy persistence + BM25 tokenizer
│   ├── retriever.py           # Hybrid (FAISS vector + BM25) RRF fusion
│   ├── generator.py           # LLM answer generation with citations
│   ├── benchmark.py           # Chunk-size / strategy comparison
│   └── models.py              # Chunk, Citation, RAGQueryResult
├── agent/                     # Multi-agent workflow
│   ├── __init__.py            # BaseAgent, AgentStep, AgentResult
│   ├── orchestrator.py        # Orchestrator (linear DAG: decompose→plan→search→synthesize)
│   ├── agent_decomposer.py    # Regex-based sub-question splitting
│   ├── agent_planner.py       # Maps sub-questions to RAG/KG steps
│   ├── agent_retriever.py     # Calls RAG pipeline + KG query
│   ├── agent_synthesizer.py   # Merges all step outputs
│   └── agent_workflow.py      # Generates Mermaid workflow diagram
├── report/                    # Report generation
│   └── generator.py           # Reads system status → Markdown report
└── api/                       # FastAPI routers
    ├── graph_routes.py        # /api/graph/* (nodes, edges, build, query, merge)
    ├── hierarchy_routes.py    # /api/graph/hierarchy/* (build, summary)
    ├── ingestion_routes.py    # /api/ingestion/* (upload, list, delete)
    ├── rag_routes.py          # /api/rag/* (index, query, status)
    ├── agent_routes.py        # /api/agent/* (query, stream SSE)
    ├── settings_routes.py     # GET /api/settings (read-only)
    └── report_routes.py       # GET /api/report/markdown
```

### Frontend (`frontend/src/`) — Vue 3 + Vite

```
src/
├── main.js                    # App entry (router mount)
├── App.vue                    # Shell: topbar tabs + RouterView + statusbar
├── router/index.js            # 6 routes (/ → knowledge-graph default)
├── api/client.js              # Axios instance + all API functions
├── styles/main.css            # Global CSS
├── views/
│   ├── KnowledgeGraphView.vue # Graph + level switcher + drill/breadcrumb
│   ├── RAGQueryView.vue       # Q&A panel + citations
│   ├── KnowledgeMergeView.vue # Merge candidates + confirm UI
│   ├── AgentView.vue          # SSE workflow + Mermaid diagram
│   ├── ReportView.vue         # Markdown render
│   └── SettingsView.vue       # Upload + local prefs
└── components/
    ├── GraphCanvas.vue         # Cytoscape.js wrapper (force layout, level shapes, highlight)
    ├── GraphFilter.vue         # Category/relation/layout controls
    ├── GraphBreadcrumb.vue     # Drill-path navigation
    ├── LevelSwitcher.vue       # Book/Chapter/Knowledge level toggle
    ├── ChatPanel.vue           # RAG/Agent conversation
    ├── CitationCard.vue        # Source reference card
    └── UploadZone.vue          # Drag-drop file upload
```

### Data Flow

```
Upload → Parsed JSON (data/parsed/*.json)
  ├── Graph Builder → nodes.json / edges.json (data/knowledge_graph/)
  │   └── Hierarchy Builder → level=book/chapter/knowledge nodes
  └── RAG Chunker → chunks.json / embeddings.npy (data/chunks/)
      └── Hybrid Retriever (vector + BM25, RRF) → LLM Generation

Knowledge Graph has 3 levels: book / chapter / knowledge, all in same JSON files
with `level` field as discriminator. Book-book and chapter-chapter edges use
token-level Jaccard similarity (≥ 0.06).
```

## Key Patterns

### LLM Client
- `GraphLLMClient` wraps OpenAI-compatible API, always uses `response_format={"type": "json_object"}`, temperature=0.1
- LLM config flows from frontend localStorage → API request body (`llm_config` field) → backend
- Every LLM call has a rule-based fallback

### GraphStore Persistence
- All graph data in flat JSON files: `nodes.json`, `edges.json`
- `upsert(textbook_id)` replaces only `level="knowledge"` nodes for that textbook
- `upsert_level(level)` replaces an entire hierarchy level
- NetworkX `DiGraph` available via `as_networkx()` but query engine uses its own BFS

### Three-Layer Knowledge Granularity
- `level` field on every KnowledgeNode/KnowledgeEdge: "book" | "chapter" | "knowledge"
- Book level: auto-generated from parsed TextbookSchema
- Chapter level: auto-generated from ChapterSchema
- Knowledge level: LLM-extracted concepts
- Drill interaction: click book → chapter → knowledge, breadcrumb navigates back
- Book-book and chapter-chapter edges computed from keyword token overlap (no LLM)

### Merge Workflow
- Two-phase: `preview()` generates LLM decisions → `confirm()` applies user-approved merges
- Dedup via SequenceMatcher on normalized names + definitions

## Git Conventions

```
type:(scope) description

add:   New feature
fix:   Bug fix
feat:  Enhancement of existing feature

Examples:
  add:(hierarchy) three-layer knowledge granularity with drill-down UI
  fix:(graph-canvas) resolve flash-to-corner bug
```
