"""Wires validator -> triage -> agent dispatch -> auditor -> contradiction ->
self-learning -> trajectory/memory logging together.

This is the single entry point the UI and evaluation scorecard call.
"""
from dataclasses import dataclass
from typing import Optional

from agents.anomaly_detection import run_anomaly_detection
from agents.auditor import audit_agent_response
from agents.contradiction import check_contradiction
from agents.cost_analysis import run_cost_analysis
from agents.simulator import run_simulation
from agents.trend_analysis import run_trend_analysis
from agents.triage import triage
from core.memory import Memory
from core.self_learning import SelfLearning
from core.session import Session
from core.trajectory import Trajectory
from sandbox.safe_executor import safe_execute
from tools.csv_reader import summarize_report
from tools.validator import validate_input
from tools.visualizer import generate_chart

CONTRADICTION_LOOKBACK = 3

VERIFIED_LABELS = {"anomaly_detection", "trend_analysis", "simulation"}

AGENT_DISPATCH = {
    "anomaly_detection": lambda filepath, question, prefs: run_anomaly_detection(filepath, question, prefs),
    "trend_analysis": lambda filepath, question, prefs: run_trend_analysis(filepath, question, prefs),
    "cost_analysis": lambda filepath, question, prefs: run_cost_analysis(question, prefs),
    "simulation": lambda filepath, question, prefs: run_simulation(filepath, question, prefs),
}
# NOTE: the spec for this rename left "simulation" out of DATA_REQUIRED_LABELS. Kept it in --
# the simulator reads the uploaded dataframe, so dropping it would crash run_simulation(None, ...)
# the first time someone asks a what-if question without a file.
DATA_REQUIRED_LABELS = {"anomaly_detection", "trend_analysis", "visualization", "simulation"}
LLM_CALL_TIMEOUT_SECONDS = 60  # generate()'s own retry/backoff can take up to ~45s


@dataclass
class PipelineResult:
    agent: str
    answer: str
    trajectory: Trajectory
    chart_path: Optional[str] = None
    # Proactive (CFO briefing) analysis is upload-triggered in the UI, not computed per
    # question here -- see ui/app.py. This field exists for API-shape parity but run_pipeline
    # never populates it itself.
    proactive: Optional[dict] = None
    performance_report: Optional[str] = None


def _extract_confidence(answer: str) -> int:
    for line in answer.splitlines():
        if line.strip().upper().startswith("CONFIDENCE:"):
            digits = "".join(ch for ch in line.split(":", 1)[1] if ch.isdigit())
            if digits:
                return int(digits[:3])
    return 0


def _finish(
    agent: str,
    answer: str,
    traj: Trajectory,
    memory: Memory,
    sl: SelfLearning,
    session: Optional[Session] = None,
    question: str = "",
    audit_verdict: str = "",
    chart_path: Optional[str] = None,
) -> PipelineResult:
    memory.log_history(agent, answer)
    if session is not None:
        session.log(question, agent, answer, audit_verdict)
    return PipelineResult(agent, answer, traj, chart_path, None, sl.get_performance_report())


def run_pipeline(
    question: str,
    filepath: Optional[str] = None,
    memory: Optional[Memory] = None,
    session: Optional[Session] = None,
) -> PipelineResult:
    memory = memory or Memory()
    sl = SelfLearning()
    traj = Trajectory()

    validation = validate_input(question)
    traj.record("router", "validator", validation.ok, validation.reason)
    if not validation.ok:
        return _finish("blocked", validation.reason, traj, memory, sl, session, question)

    label_result = safe_execute(triage, question, timeout=LLM_CALL_TIMEOUT_SECONDS)
    traj.record("triage", "triage", label_result.success, label_result.error or "")
    if not label_result.success:
        return _finish("blocked", f"Triage failed: {label_result.error}", traj, memory, sl, session, question)

    label = label_result.output

    hint = sl.get_routing_hint(question)
    if hint and hint != label:
        traj.record("self_learning", "routing_hint", True, f"learned={hint}, triage={label}")

    if label not in AGENT_DISPATCH and label != "visualization":
        traj.record("router", "dispatch", False, f"unknown label '{label}'")
        return _finish(label, f"Could not route question (label={label}).", traj, memory, sl, session, question)

    if label in DATA_REQUIRED_LABELS and not filepath:
        traj.record("router", "dispatch", False, "no file provided")
        return _finish(label, "This question needs a CSV report — please upload one.", traj, memory, sl, session, question)

    if label == "visualization":
        exec_result = safe_execute(generate_chart, filepath)
        traj.record(label, "generate_chart", exec_result.success, exec_result.error or "")
        if not exec_result.success:
            return _finish(label, f"Chart generation failed: {exec_result.error}", traj, memory, sl, session, question)
        return _finish(label, "Chart generated.", traj, memory, sl, session, question, chart_path=exec_result.output)

    preferences = memory.get_preferences(label)
    exec_result = safe_execute(AGENT_DISPATCH[label], filepath, question, preferences, timeout=LLM_CALL_TIMEOUT_SECONDS)
    traj.record(label, "agent_call", exec_result.success, exec_result.error or "")

    answer = exec_result.output if exec_result.success else f"Agent failed: {exec_result.error}"
    audit_verdict = ""

    if exec_result.success and filepath and label in VERIFIED_LABELS:
        data_summary = summarize_report(filepath)
        audit_result = safe_execute(audit_agent_response, question, label, data_summary, answer, timeout=60)
        detail = audit_result.error or (audit_result.output or {}).get("verdict", "")
        traj.record("auditor", "audit_agent_response", audit_result.success, detail)
        if audit_result.success:
            audit_verdict = audit_result.output["verdict"]
            if not audit_result.output["passed"]:
                answer += f"\n\n⚠️ Auditor check FAILED: {audit_result.output['raw']}"

        sl.record_result(
            question=question,
            routed_to=label,
            audit_verdict=audit_verdict or "UNKNOWN",
            confidence=_extract_confidence(answer),
        )

    if exec_result.success and label in VERIFIED_LABELS and session is not None:
        prior = [e for e in session.entries if e.agent == label][-CONTRADICTION_LOOKBACK:]
        if prior:
            contradiction_result = safe_execute(check_contradiction, question, answer, prior, timeout=60)
            traj.record("contradiction", "check_contradiction", contradiction_result.success, contradiction_result.error or "")
            if contradiction_result.success and contradiction_result.output:
                answer += f"\n\n⚠️ CONTRADICTION: {contradiction_result.output}"

    return _finish(label, answer, traj, memory, sl, session, question, audit_verdict)
