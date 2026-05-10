"""FastAPI entrypoint for Agent4Study."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.ingestion_routes import router as ingestion_router
from src.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered textbook knowledge integration system.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion_router)


@app.get("/health", tags=["system"])
def health_check() -> dict:
    """Return backend readiness and placeholder module states."""

    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "stage": "task1-scaffold",
        "modules": {
            "ingestion": "placeholder",
            "knowledge_graph": "placeholder",
            "rag": "placeholder",
            "agent": "placeholder",
            "report": "placeholder",
        },
    }
