"""Question decomposition agent."""

import re

from src.agent import BaseAgent


class DecomposerAgent(BaseAgent):
    name = "Decomposer"

    def run(self, question: str) -> list[str]:
        parts = [part.strip() for part in re.split(r"[？?。；;，,]|和|以及|并且", question) if part.strip()]
        if not parts:
            return [question]
        if len(parts) == 1 and len(question) > 28:
            return [question, f"请补充与“{question[:16]}”相关的知识关系"]
        return parts[:5]
