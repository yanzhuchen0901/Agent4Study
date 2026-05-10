"""RAG API routes."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.config import get_settings
from src.ingestion.models import TextbookSchema
from src.rag.chunker import RecursiveChunker
from src.rag.embedder import Embedder
from src.rag.generator import RAGGenerator
from src.rag.models import RAGIndexResult, RAGQueryResult, RAGStatus
from src.rag.retriever import HybridRetriever
from src.rag.vector_store import VectorStore


router = APIRouter(prefix="/api/rag", tags=["rag"])


class RAGIndexRequest(BaseModel):
    textbook_id: str


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("/index", response_model=RAGIndexResult)
def index_textbook(request: RAGIndexRequest) -> RAGIndexResult:
    settings = get_settings()
    parsed_path = settings.parsed_dir / f"{request.textbook_id}.json"
    if not parsed_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parsed textbook not found")

    textbook = TextbookSchema.model_validate_json(parsed_path.read_text(encoding="utf-8"))
    chunks = RecursiveChunker().chunk_textbook(textbook)
    if not chunks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No chunks generated")

    embedder = Embedder()
    embeddings = embedder.encode([chunk.content for chunk in chunks])
    VectorStore().save(chunks, embeddings)
    return RAGIndexResult(
        status="indexed",
        textbook_id=request.textbook_id,
        chunks=len(chunks),
        dimension=int(embeddings.shape[1]),
    )


@router.post("/query", response_model=RAGQueryResult)
def query_rag(request: RAGQueryRequest) -> RAGQueryResult:
    if not request.query.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query is required")
    top_k = max(1, min(request.top_k, 10))
    retrieved = HybridRetriever().retrieve(request.query.strip(), top_k=top_k)
    return RAGGenerator().generate(request.query.strip(), retrieved)


@router.get("/status", response_model=RAGStatus)
def rag_status() -> RAGStatus:
    chunks, dimension, textbook_ids = VectorStore().status()
    return RAGStatus(indexed=chunks > 0, chunks=chunks, dimension=dimension, textbook_ids=textbook_ids)
