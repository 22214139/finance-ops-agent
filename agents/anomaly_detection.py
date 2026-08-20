"""Anomaly detection agent: flags statistical anomalies in a report and explains them."""
import pandas as pd

from core.llm_client import generate
from tools.csv_reader import load_dataframe

ANOMALY_STD_THRESHOLD = 2.0

ANOMALY_PROMPT = """You are a financial anomaly detection agent. Review the anomaly findings below
and the user's question, then explain what looks unusual and why it matters.

ANOMALIES FOUND:
{anomalies}

USER PREFERENCES:
{preferences}

QUESTION:
{question}

Be specific: name the row/column and the deviation. If no anomalies were found, say so plainly.

Respond in exactly this format:
ANSWER: <your explanation>
CONFIDENCE: <0-100, how confident you are the answer is fully grounded in the anomaly findings above>
GROUNDED: YES or NO
SOURCE ROWS: <comma-separated labels/rows the answer is based on, or "none" if no anomalies>"""


def detect_anomalies(df: pd.DataFrame, std_threshold: float = ANOMALY_STD_THRESHOLD) -> list[str]:
    label_col = next((c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])), None)

    findings = []
    numeric_cols = df.select_dtypes(include="number").columns
    for col in numeric_cols:
        mean, std = df[col].mean(), df[col].std()
        if not std or pd.isna(std):
            continue
        deviations = (df[col] - mean).abs() / std
        for idx in df.index[deviations > std_threshold]:
            label = f"{df.loc[idx, label_col]} " if label_col else ""
            findings.append(
                f"Row {idx} {label}({col}={df.loc[idx, col]}): "
                f"{deviations[idx]:.1f} std devs from mean ({mean:.2f})"
            )
    return findings


def run_anomaly_detection(filepath: str, question: str, preferences: list[str] | None = None) -> str:
    df = load_dataframe(filepath)
    anomalies = detect_anomalies(df)
    anomalies_text = "\n".join(anomalies) if anomalies else "No anomalies found above threshold."
    prompt = ANOMALY_PROMPT.format(
        anomalies=anomalies_text,
        preferences="\n".join(preferences) if preferences else "None",
        question=question,
    )
    return generate(prompt)
