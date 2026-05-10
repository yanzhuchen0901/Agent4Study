"""Final answer synthesis agent."""

from src.agent import AgentStep, BaseAgent


class SynthesizerAgent(BaseAgent):
    name = "Synthesizer"

    def run(self, input_data: dict) -> dict:
        question: str = input_data["question"]
        steps: list[AgentStep] = input_data["steps"]
        citations: list[dict] = []
        fragments: list[str] = []

        for step in steps:
            if step.type == "rag" and isinstance(step.output, dict):
                if step.output.get("answer"):
                    fragments.append(f"RAG: {step.output['answer']}")
                citations.extend(step.output.get("citations", []))
            if step.type == "kg" and isinstance(step.output, dict):
                if step.output.get("answer"):
                    fragments.append(f"图谱: {step.output['answer']}")

        if not fragments:
            answer = "当前知识库中未找到足够信息回答该问题。"
        else:
            answer = f"问题：{question}\n\n" + "\n\n".join(fragments)
        return {"answer": answer, "citations": citations}
