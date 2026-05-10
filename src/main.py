"""FastAPI entrypoint for Agent4Study."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.agent_routes import router as agent_router
from src.api.graph_routes import router as graph_router
from src.api.hierarchy_routes import router as hierarchy_router
from src.api.ingestion_routes import router as ingestion_router
from src.api.rag_routes import router as rag_router
from src.api.report_routes import router as report_router
from src.api.settings_routes import router as settings_router
from src.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered textbook knowledge integration system.",
)

_cors_default = (
    "http://localhost:5173,http://localhost:5174,"
    "http://127.0.0.1:5173,http://127.0.0.1:5174"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", _cors_default).split(",")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion_router)
app.include_router(graph_router)
app.include_router(hierarchy_router)
app.include_router(rag_router)
app.include_router(agent_router)
app.include_router(settings_router)
app.include_router(report_router)


@app.get("/health", tags=["system"])
def health_check() -> dict:
    """Return backend readiness and placeholder module states."""

    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "stage": "task8-complete",
        "modules": {
            "ingestion": "ready",
            "knowledge_graph": "ready",
            "rag": "ready",
            "agent": "ready",
            "report": "ready",
        },
    }
