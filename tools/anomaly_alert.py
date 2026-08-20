"""Auto anomaly alert: runs the moment a CSV is uploaded, independent of any question.

Reuses the same std-deviation threshold as agents/audit.py so "flagged on upload" and
"flagged when the audit agent is asked" never disagree — just phrased for a banner instead
of an LLM prompt.
"""
import pandas as pd

from agents.anomaly_detection import ANOMALY_STD_THRESHOLD
from tools.csv_reader import load_dataframe


def check_on_upload(filepath: str, std_threshold: float = ANOMALY_STD_THRESHOLD) -> str:
    if not filepath:
        return ""

    df = load_dataframe(filepath)
    label_col = next((c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])), None)
    numeric_cols = df.select_dtypes(include="number").columns

    alerts = []
    for col in numeric_cols:
        mean, std = df[col].mean(), df[col].std()
        if not std or pd.isna(std):
            continue
        deviations = (df[col] - mean).abs() / std
        for idx in df.index[deviations > std_threshold]:
            value = df.loc[idx, col]
            pct = (value - mean) / mean * 100 if mean else 0.0
            label = df.loc[idx, label_col] if label_col else f"row {idx}"
            direction = "below" if pct < 0 else "above"
            alerts.append(
                f"AUTO-ALERT: {label} {col} (${value:,.0f}) is {abs(pct):.0f}% {direction} "
                f"the {len(df)}-period average (${mean:,.0f}). Flagged for review."
            )

    return "\n".join(alerts) if alerts else "No anomalies detected on upload."
