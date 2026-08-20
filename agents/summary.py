"""Executive summary: aggregates the current session's entries into a short report.
Counts and pass/fail rates are computed directly from logged entries, not guessed by an LLM.
"""
from core.session import Session

ANSWERED_LABELS = ("research", "audit", "simulation")


def _answer_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip().upper().startswith("ANSWER:"):
            return line.split(":", 1)[1].strip()
    first_line = text.strip().splitlines()
    return first_line[0] if first_line else "N/A"


def generate_session_summary(session: Session) -> str:
    questions = [e for e in session.entries if e.agent != "anomaly_alert"]
    if not questions:
        return "No questions asked yet this session."

    agent_counts: dict[str, int] = {}
    for e in questions:
        agent_counts[e.agent] = agent_counts.get(e.agent, 0) + 1
    agents_line = ", ".join(f"{agent}({count})" for agent, count in agent_counts.items())

    audited = [e for e in questions if e.audit_verdict]
    audit_pass = sum(1 for e in audited if e.audit_verdict == "PASS")

    last_answered = next((e for e in reversed(questions) if e.agent in ANSWERED_LABELS), None)
    key_insight = _answer_line(last_answered.answer) if last_answered else "N/A"

    anomaly_count = sum(
        e.answer.count("AUTO-ALERT") for e in session.entries if e.agent == "anomaly_alert"
    )

    lines = [
        "SESSION SUMMARY",
        "---------------",
        f"Questions asked: {len(questions)}",
        f"Agents used: {agents_line}",
    ]
    if audited:
        lines.append(f"Audit results: {audit_pass}/{len(audited)} PASS")
    lines.append(f"Key insight: {key_insight}")
    lines.append(f"Anomalies detected: {anomaly_count}")
    return "\n".join(lines)
