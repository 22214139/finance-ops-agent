"""Tracks each step of a workflow run for a post-hoc audit trail."""
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class Step:
    agent: str
    tool: str
    success: bool
    timestamp: float
    detail: str = ""


class Trajectory:
    def __init__(self):
        self.steps: list[Step] = []

    def record(self, agent: str, tool: str, success: bool, detail: str = "") -> None:
        self.steps.append(Step(agent=agent, tool=tool, success=success, timestamp=time.time(), detail=detail))

    def validator_ran_first(self) -> bool:
        return bool(self.steps) and self.steps[0].tool == "validator"

    def first_failure(self) -> Optional[Step]:
        for step in self.steps:
            if not step.success:
                return step
        return None

    def summary(self) -> str:
        lines = []
        for i, step in enumerate(self.steps, 1):
            status = "OK" if step.success else "FAIL"
            ts = time.strftime("%H:%M:%S", time.localtime(step.timestamp))
            detail = f" ({step.detail})" if step.detail else ""
            lines.append(f"{i}. [{ts}] {step.agent}.{step.tool} -> {status}{detail}")

        failure = self.first_failure()
        lines.append("")
        lines.append(f"Validator ran first: {self.validator_ran_first()}")
        lines.append(f"First failure: {failure.tool if failure else 'none'}")
        return "\n".join(lines)
