"""Research agent: trend analysis and period-over-period comparisons."""
from core.llm_client import generate
from tools.csv_reader import load_dataframe

RESEARCH_PROMPT = """You are a financial research agent. Analyze the data below to answer
the question. Be data-driven, cite specific numbers, and call out the trend direction.

DATA:
{data}

USER PREFERENCES:
{preferences}

QUESTION:
{question}

Respond in exactly this format:
ANSWER: <your answer, citing specific numbers from the data>
CONFIDENCE: <0-100, how confident you are the answer is fully grounded in the data above>
GROUNDED: YES or NO
SOURCE ROWS: <comma-separated labels/rows the answer is based on>"""


def run_research(filepath: str, question: str, preferences: list[str] | None = None) -> str:
    df = load_dataframe(filepath)
    prompt = RESEARCH_PROMPT.format(
        data=df.to_string(index=False),
        preferences="\n".join(preferences) if preferences else "None",
        question=question,
    )
    return generate(prompt)
