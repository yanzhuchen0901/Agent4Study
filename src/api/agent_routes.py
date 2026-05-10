"""Agent workflow API routes."""

import json

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from src.agent import AgentResult
from src.agent.orchestrator import AgentOrchestrator
from src.agent.agent_workflow import build_workflow_mermaid


router = APIRouter(prefix="/api/agent", tags=["agent"])


class AgentQueryRequest(BaseModel):
    question: str
    llm_config: dict | None = None


@router.post("/query", response_model=AgentResult)
def query_agent(request: AgentQueryRequest) -> AgentResult:
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question is required")
    return AgentOrchestrator(llm_config=request.llm_config).run(question)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/query/stream")
def stream_agent_query(question: str) -> StreamingResponse:
    cleaned = question.strip()
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question is required")

    def event_stream():
        orchestrator = AgentOrchestrator()
        sub_questions, _ = orchestrator.plan(cleaned)
        executed = []
        yield _sse("started", {"question": cleaned, "sub_questions": sub_questions})
        try:
            for step in orchestrator.iter_steps(cleaned):
                executed.append(step)
                yield _sse("step", step.model_dump())
            synthesized = orchestrator.synthesizer.run({"question": cleaned, "steps": executed})
            result = AgentResult(
                question=cleaned,
                sub_questions=sub_questions,
                steps=executed,
                answer=synthesized["answer"],
                citations=synthesized["citations"],
                workflow_mermaid=build_workflow_mermaid(executed),
            )
            yield _sse("completed", result.model_dump())
        except Exception as exc:
            yield _sse("error", {"detail": str(exc)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
