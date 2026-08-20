"""Triage agent: classifies a user's finance question and routes it to one agent."""
from core.llm_client import generate

CATEGORIES = ["anomaly_detection", "trend_analysis", "cost_analysis", "visualization", "simulation"]

TRIAGE_PROMPT = """Classify this finance question into exactly one category:
- anomaly_detection: errors, irregularities, invoice validation, unusual/unexpected values
- trend_analysis: comparing months, best/worst month, profit patterns, performance over time
- cost_analysis: expenses, vendors, purchase orders, cost reduction
- visualization: ONLY when the user explicitly asks to see a chart, graph, plot, or picture
- simulation: ONLY hypothetical "what if" questions proposing a change (e.g. "what if we reduce
  expenses by 10% in March", "what if revenue grew 5%") and asking for the projected effect

Choose visualization only if the request names a visual (e.g. "show me a chart", "plot this",
"graph the trend"). A question that could merely be illustrated by a chart, but doesn't ask for
one, is NOT visualization — classify it by what it's actually asking for instead.

Choose simulation only if the question proposes a hypothetical change and asks what would
happen. A question that merely asks about the existing trend, without proposing a change, is
trend_analysis instead.

Question: {question}

Return only the category name, nothing else."""


def triage(question: str) -> str:
    response = generate(TRIAGE_PROMPT.format(question=question))
    label = response.strip().lower()
    for category in CATEGORIES:
        if category in label:
            return category
    return "trend_analysis"
