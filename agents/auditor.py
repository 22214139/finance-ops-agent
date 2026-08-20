"""Auditor agent: independently verifies research/audit agent answers before they reach the user."""
from core.llm_client import generate

AUDITOR_PROMPT = """You are a verification auditor for a financial analysis system. An agent
already answered a question; your job is to independently check that answer against the data,
not to answer the question yourself.

ORIGINAL QUESTION:
{question}

AGENT USED:
{agent_used}

DATA:
{data_summary}

AGENT'S ANSWER:
{agent_answer}

Check:
1. Are all numbers in the answer actually present in or derivable from the data?
2. Does the answer invent any fact not supported by the data (hallucination)?
3. Was the right kind of agent used for this question?
4. Is the conclusion logically consistent with the data?

Respond in exactly this format, nothing else:
VERDICT: PASS or FAIL
GROUNDED: YES or NO
HALLUCINATION: YES or NO
REASON: <one sentence>"""


def _parse_field(text: str, field: str) -> str:
    for line in text.splitlines():
        if line.strip().upper().startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    return ""


def audit_agent_response(question: str, agent_used: str, data_summary: str, agent_answer: str) -> dict:
    try:
        prompt = AUDITOR_PROMPT.format(
            question=question,
            agent_used=agent_used,
            data_summary=data_summary,
            agent_answer=agent_answer,
        )
        raw = generate(prompt)

        verdict = "PASS" if _parse_field(raw, "VERDICT").upper().startswith("PASS") else "FAIL"
        grounded = _parse_field(raw, "GROUNDED").upper().startswith("YES")
        hallucination = _parse_field(raw, "HALLUCINATION").upper().startswith("YES")

        return {
            "verdict": verdict,
            "grounded": grounded,
            "hallucination": hallucination,
            "raw": raw,
            "passed": verdict == "PASS",
        }
    except Exception as e:
        return {
            "verdict": "FAIL",
            "grounded": False,
            "hallucination": False,
            "raw": f"Auditor error: {type(e).__name__}: {e}",
            "passed": False,
        }
