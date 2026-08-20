"""What-if simulator: the LLM only extracts scenario parameters (column/period/percent);
every actual number in the answer is computed by pandas, never guessed by the LLM.
"""
import pandas as pd

from core.llm_client import generate
from tools.csv_reader import load_dataframe

EXTRACT_PROMPT = """Extract the parameters of this what-if financial scenario.

AVAILABLE COLUMNS: {columns}
AVAILABLE PERIODS: {periods}

QUESTION:
{question}

Respond in exactly this format, nothing else:
COLUMN: <one of the available columns being changed>
PERIOD: <one exact value from the available periods, or ALL if it applies to every period>
PERCENT: <signed number, e.g. -10 for a 10% reduction, 15 for a 15% increase>"""


def _parse_field(text: str, field: str) -> str:
    for line in text.splitlines():
        if line.strip().upper().startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    return ""


def run_simulation(filepath: str, question: str, preferences: list[str] | None = None) -> str:
    df = load_dataframe(filepath)
    label_col = next((c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])), None)
    numeric_cols = list(df.select_dtypes(include="number").columns)
    periods = list(df[label_col].astype(str)) if label_col else [str(i) for i in df.index]

    raw = generate(EXTRACT_PROMPT.format(
        columns=", ".join(numeric_cols), periods=", ".join(periods), question=question
    ))
    column = _parse_field(raw, "COLUMN").strip()
    period = _parse_field(raw, "PERIOD").strip()
    percent_text = _parse_field(raw, "PERCENT").strip().replace("%", "")

    if column not in numeric_cols:
        return f"Could not identify which column to simulate (got '{column}')."
    try:
        percent = float(percent_text)
    except ValueError:
        return f"Could not parse a percentage from the question (got '{percent_text}')."

    if label_col and period.upper() != "ALL":
        mask = df.index[df[label_col].astype(str).str.lower() == period.lower()]
        if len(mask) == 0:
            return f"Could not find period '{period}' in the data. Available: {', '.join(periods)}."
    else:
        mask = df.index

    working = df.copy()
    old_values = df.loc[mask, column]
    new_values = old_values * (1 + percent / 100)
    working.loc[mask, column] = new_values

    lines = [
        f"{working.loc[idx, label_col] if label_col else f'row {idx}'}: "
        f"{column} ${old_values[idx]:,.0f} -> ${new_values[idx]:,.0f}"
        for idx in mask
    ]
    result = "WHAT-IF RESULT:\n" + "\n".join(lines)

    if {"revenue", "expenses", "profit"}.issubset(numeric_cols) and column in ("revenue", "expenses"):
        old_profit = df.loc[mask, "profit"].sum()
        new_profit = (working.loc[mask, "revenue"] - working.loc[mask, "expenses"]).sum()
        pct_change = (new_profit - old_profit) / old_profit * 100 if old_profit else 0.0
        result += f"\n\nPROFIT IMPACT: ${old_profit:,.0f} -> ${new_profit:,.0f} ({pct_change:+.1f}%)"

    return result
