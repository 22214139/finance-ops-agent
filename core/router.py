"""Wires validator -> triage -> agent dispatch -> trajectory/memory logging together.

This is the single entry point the UI and evaluation scorecard call.
"""
from dataclasses import dataclass
from typing import Optional

from agents.audit import run_audit
from agents.procurement import run_procurement
from agents.research import run_research
from agents.triage import triage
from core.memory import Memory
from core.trajectory import Trajectory
from sandbox.safe_executor import safe_execute
from tools.validator import validate_input
from tools.visualizer import generate_chart

AGENT_DISPATCH = {
    "audit": lambda filepath, question, prefs: run_audit(filepath, question, prefs),
    "research": lambda filepath, question, prefs: run_research(filepath, question, prefs),
    "procurement": lambda filepath, question, prefs: run_procurement(question, prefs),
}
DATA_REQUIRED_LABELS = {"audit", "research", "visualization"}
LLM_CALL_TIMEOUT_SECONDS = 60  # generate()'s own retry/backoff can take up to ~45s


@dataclass
class PipelineResult:
    agent: str
    answer: str
    trajectory: Trajectory
    chart_path: Optional[str] = None


def _finish(agent: str, answer: str, traj: Trajectory, memory: Memory, chart_path: Optional[str] = None) -> PipelineResult:
    memory.log_history(agent, answer)
    return PipelineResult(agent, answer, traj, chart_path)


def run_pipeline(question: str, filepath: Optional[str] = None, memory: Optional[Memory] = None) -> PipelineResult:
    memory = memory or Memory()
    traj = Trajectory()

    validation = validate_input(question)
    traj.record("router", "validator", validation.ok, validation.reason)
    if not validation.ok:
        return _finish("blocked", validation.reason, traj, memory)

    label_result = safe_execute(triage, question, timeout=LLM_CALL_TIMEOUT_SECONDS)
    traj.record("triage", "triage", label_result.success, label_result.error or "")
    if not label_result.success:
        return _finish("blocked", f"Triage failed: {label_result.error}", traj, memory)

    label = label_result.output

    if label not in AGENT_DISPATCH and label != "visualization":
        traj.record("router", "dispatch", False, f"unknown label '{label}'")
        return _finish(label, f"Could not route question (label={label}).", traj, memory)

    if label in DATA_REQUIRED_LABELS and not filepath:
        traj.record("router", "dispatch", False, "no file provided")
        return _finish(label, "This question needs a CSV report — please upload one.", traj, memory)

    if label == "visualization":
        exec_result = safe_execute(generate_chart, filepath)
        traj.record(label, "generate_chart", exec_result.success, exec_result.error or "")
        if not exec_result.success:
            return _finish(label, f"Chart generation failed: {exec_result.error}", traj, memory)
        return _finish(label, "Chart generated.", traj, memory, chart_path=exec_result.output)

    preferences = memory.get_preferences(label)
    exec_result = safe_execute(AGENT_DISPATCH[label], filepath, question, preferences, timeout=LLM_CALL_TIMEOUT_SECONDS)
    traj.record(label, "agent_call", exec_result.success, exec_result.error or "")

    answer = exec_result.output if exec_result.success else f"Agent failed: {exec_result.error}"
    return _finish(label, answer, traj, memory)
