"""Agent workflow orchestrator."""

from src.agent import AgentResult, AgentStep
from src.agent.agent_decomposer import DecomposerAgent
from src.agent.agent_planner import PlannerAgent
from src.agent.agent_retriever import KnowledgeGraphAgent, SearcherAgent
from src.agent.agent_synthesizer import SynthesizerAgent
from src.agent.agent_workflow import build_workflow_mermaid


class AgentOrchestrator:
    def __init__(self) -> None:
        self.decomposer = DecomposerAgent()
        self.planner = PlannerAgent()
        self.searcher = SearcherAgent()
        self.kg_agent = KnowledgeGraphAgent()
        self.synthesizer = SynthesizerAgent()

    def run(self, question: str) -> AgentResult:
        executed = list(self.iter_steps(question))
        sub_questions = self.decomposer.run(question)
        synthesized = self.synthesizer.run({"question": question, "steps": executed})
        return AgentResult(
            question=question,
            sub_questions=sub_questions,
            steps=executed,
            answer=synthesized["answer"],
            citations=synthesized["citations"],
            workflow_mermaid=build_workflow_mermaid(executed),
        )

    def plan(self, question: str) -> tuple[list[str], list[AgentStep]]:
        sub_questions = self.decomposer.run(question)
        return sub_questions, self.planner.run(sub_questions)

    def iter_steps(self, question: str):
        _, steps = self.plan(question)
        for step in steps:
            try:
                step.status = "running"
                if step.type == "rag":
                    step.output = self.searcher.run(step.query)
                elif step.type == "kg":
                    step.output = self.kg_agent.run(step.query)
                step.status = "completed"
            except Exception as exc:
                step.status = "failed"
                step.output = {"error": str(exc)}
            yield step
