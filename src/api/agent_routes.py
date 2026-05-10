"""Agent workflow API routes."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.agent import AgentResult
from src.agent.orchestrator import AgentOrchestrator


router = APIRouter(prefix="/api/agent", tags=["agent"])


class AgentQueryRequest(BaseModel):
    question: str


@router.post("/query", response_model=AgentResult)
def query_agent(request: AgentQueryRequest) -> AgentResult:
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question is required")
    return AgentOrchestrator().run(question)
