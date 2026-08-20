"""Cost analysis agent: expense/vendor review and purchase order drafting."""
from dataclasses import dataclass

from core.llm_client import generate

PO_PROMPT = """You are a cost analysis agent. Draft a purchase order from the request below.

REQUEST:
{question}

USER PREFERENCES:
{preferences}

Return the purchase order in exactly this format:
PO Number: <placeholder like PO-0001>
Vendor: <vendor name>
Items: <item, quantity, unit price>
Total: <total amount>
Notes: <caveats, e.g. missing info the requester should confirm>"""


@dataclass
class POValidationResult:
    ok: bool
    reason: str


def validate_po_request(question: str) -> POValidationResult:
    if not question or not question.strip():
        return POValidationResult(False, "Blocked: empty procurement request.")
    return POValidationResult(True, "ok")


def run_cost_analysis(question: str, preferences: list[str] | None = None) -> str:
    validation = validate_po_request(question)
    if not validation.ok:
        return validation.reason
    prompt = PO_PROMPT.format(
        question=question,
        preferences="\n".join(preferences) if preferences else "None",
    )
    return generate(prompt)
