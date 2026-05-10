"""Agent workflow package."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class AgentStep(BaseModel):
    name: str
    type: str
    query: str
    status: str = "pending"
    output: Any = None


class AgentResult(BaseModel):
    question: str
    sub_questions: list[str]
    steps: list[AgentStep]
    answer: str
    citations: list[dict] = Field(default_factory=list)
    workflow_mermaid: str


class BaseAgent(ABC):
    name: str

    @abstractmethod
    def run(self, input_data: Any) -> Any:
        """Run the agent with structured input."""
