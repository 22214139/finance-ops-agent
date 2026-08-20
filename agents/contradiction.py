"""Contradiction detector: checks whether the newest research/audit/simulation answer
logically conflicts with an earlier answer from the same session.
"""
from core.llm_client import generate
from core.session import SessionEntry

CONTRADICTION_PROMPT = """You are checking two financial answers from the same session for a
genuine logical contradiction -- not just a different topic, but conclusions that cannot both
be true, or advice that conflicts (e.g. praising a month as the best performer, then also
recommending it as the one to cut costs from).

EARLIER Q&A:
Q: {prev_question}
A: {prev_answer}

NEWEST Q&A:
Q: {new_question}
A: {new_answer}

Respond in exactly this format, nothing else:
CONTRADICTION: YES or NO
EXPLANATION: <one sentence, empty if NO>"""


def _parse_field(text: str, field: str) -> str:
    for line in text.splitlines():
        if line.strip().upper().startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    return ""


def check_contradiction(new_question: str, new_answer: str, prior_entries: list[SessionEntry]) -> str:
    for entry in prior_entries:
        raw = generate(CONTRADICTION_PROMPT.format(
            prev_question=entry.question,
            prev_answer=entry.answer,
            new_question=new_question,
            new_answer=new_answer,
        ))
        if _parse_field(raw, "CONTRADICTION").upper().startswith("YES"):
            explanation = _parse_field(raw, "EXPLANATION")
            return explanation or "Conflicting conclusions detected against an earlier answer this session."
    return ""
