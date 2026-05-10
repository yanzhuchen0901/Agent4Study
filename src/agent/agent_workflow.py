"""Mermaid workflow generation."""

from src.agent import AgentStep


def build_workflow_mermaid(steps: list[AgentStep]) -> str:
    lines = [
        "graph TD",
        "A[用户问题] --> B[Decomposer: 问题分解]",
        "B --> C[Planner: 执行规划]",
    ]
    for index, step in enumerate(steps, 1):
        node_id = f"S{index}"
        label = f"{step.name}: {step.status}"
        lines.append(f"C --> {node_id}[{label}]")
        lines.append(f"{node_id} --> Z[Synthesizer: 综合回答]")
    lines.append("Z --> R[最终答案]")
    return "\n".join(lines)
