"""Execution planning agent."""

from src.agent import AgentStep, BaseAgent


class PlannerAgent(BaseAgent):
    name = "Planner"

    def run(self, sub_questions: list[str]) -> list[AgentStep]:
        steps: list[AgentStep] = []
        for index, query in enumerate(sub_questions, 1):
            steps.append(AgentStep(name=f"RAG 检索 {index}", type="rag", query=query))
            steps.append(AgentStep(name=f"图谱查询 {index}", type="kg", query=query))
        return steps
