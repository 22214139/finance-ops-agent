"""Triage agent: classifies a user's finance question and routes it to one agent."""
from core.llm_client import generate

CATEGORIES = ["audit", "research", "procurement", "visualization"]

TRIAGE_PROMPT = """Classify this finance question into exactly one category:
- audit: invoice validation, anomaly detection
- research: trend analysis, performance comparison, answering "which/what/how much" questions with numbers or explanation
- procurement: purchase orders, vendor management
- visualization: ONLY when the user explicitly asks to see a chart, graph, plot, or picture

Choose visualization only if the request names a visual (e.g. "show me a chart", "plot this",
"graph the trend"). A question that could merely be illustrated by a chart, but doesn't ask for
one, is NOT visualization — classify it by what it's actually asking for instead.

Question: {question}

Return only the category name, nothing else."""


def triage(question: str) -> str:
    response = generate(TRIAGE_PROMPT.format(question=question))
    label = response.strip().lower()
    for category in CATEGORIES:
        if category in label:
            return category
    return "research"
