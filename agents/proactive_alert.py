"""Proactive alert agent: on every CSV upload, automatically compares the new report
against everything uploaded before it and writes a CFO-style briefing -- no question
required. Anomaly detection, month-over-month deltas, and the next-period prediction
are all computed with pandas/scipy; only the narrative briefing itself is an LLM call.
"""
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from agents.anomaly_detection import detect_anomalies
from core.historical_memory import get_month_over_month, load_history, save_to_history
from core.llm_client import generate

PROACTIVE_ANOMALY_STD_THRESHOLD = 1.5
EXPENSE_RATIO_RISK_THRESHOLD = 0.7
EXPENSE_RATIO_RISK_STREAK = 2

BRIEFING_PROMPT = """You are a CFO AI Assistant with memory of past months.
Historical trend: {month_over_month}
This month data: {current_data}
Anomalies found: {anomalies}
Predicted next month: {predictions}
Risk alert: {risk}

Write a 3-paragraph executive briefing:
Para 1: What changed this month vs last month
Para 2: The pattern you see across all months
Para 3: What will likely happen next month and recommended action"""


def _predict_next(df: pd.DataFrame, numeric_cols) -> dict:
    predictions = {}
    x = np.arange(len(df))
    for col in numeric_cols:
        y = df[col].to_numpy(dtype=float)
        if len(y) < 2:
            continue
        fit = scipy_stats.linregress(x, y)
        predictions[col] = round(fit.intercept + fit.slope * len(df), 2)
    return predictions


def _detect_risk(df: pd.DataFrame) -> str | None:
    if "expenses" not in df.columns or "revenue" not in df.columns:
        return None
    ratio = df["expenses"] / df["revenue"].replace(0, float("nan"))
    recent = ratio.tail(EXPENSE_RATIO_RISK_STREAK)
    if len(recent) == EXPENSE_RATIO_RISK_STREAK and recent.notna().all() and (recent > EXPENSE_RATIO_RISK_THRESHOLD).all():
        return (
            f"Expenses have exceeded {EXPENSE_RATIO_RISK_THRESHOLD:.0%} of revenue for "
            f"{EXPENSE_RATIO_RISK_STREAK}+ consecutive periods."
        )
    return None


def run_proactive_analysis(filepath: str, memory=None) -> dict:
    save_to_history(filepath)
    history = load_history()

    if history is None or len(history) < 2:
        return {
            "alert": None,
            "anomalies": [],
            "predictions": {},
            "cfo_summary": "First upload — no historical comparison yet.",
            "months_analyzed": len(history) if history is not None else 0,
        }

    month_over_month = get_month_over_month(history)
    anomalies = detect_anomalies(history, std_threshold=PROACTIVE_ANOMALY_STD_THRESHOLD)
    numeric_cols = history.select_dtypes(include="number").columns
    predictions = _predict_next(history, numeric_cols)
    risk = _detect_risk(history)

    prompt = BRIEFING_PROMPT.format(
        month_over_month=month_over_month,
        current_data=history.tail(1).to_string(index=False),
        anomalies=anomalies if anomalies else "None",
        predictions=predictions,
        risk=risk or "None",
    )
    cfo_summary = generate(prompt)

    return {
        "alert": risk,
        "anomalies": anomalies,
        "predictions": predictions,
        "cfo_summary": cfo_summary,
        "months_analyzed": len(history),
    }
