"""Cross-upload historical memory: keeps a copy of every CSV a user has ever
uploaded, so later analysis can compare the current report against the trend
across all prior uploads, not just the file in front of it right now.
"""
import glob
import os
import shutil
from datetime import datetime, timezone

import pandas as pd

HISTORY_DIR = "data/history"


def save_to_history(filepath: str) -> None:
    os.makedirs(HISTORY_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    dest = os.path.join(HISTORY_DIR, f"{timestamp}_{os.path.basename(filepath)}")
    shutil.copy(filepath, dest)


def load_history() -> pd.DataFrame | None:
    files = sorted(glob.glob(os.path.join(HISTORY_DIR, "*.csv")))
    if not files:
        return None

    combined = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

    label_col = next((c for c in combined.columns if not pd.api.types.is_numeric_dtype(combined[c])), None)
    if label_col is not None:
        parsed = pd.to_datetime(combined[label_col], format="%B", errors="coerce")
        if parsed.isna().all():
            parsed = pd.to_datetime(combined[label_col], errors="coerce")
        if parsed.notna().any():
            combined = combined.assign(_sort_key=parsed).sort_values("_sort_key").drop(columns="_sort_key")

    return combined.reset_index(drop=True)


def get_month_over_month(df: pd.DataFrame) -> dict:
    if len(df) < 2:
        return {}
    numeric_cols = df.select_dtypes(include="number").columns
    prev_row, last_row = df.iloc[-2], df.iloc[-1]
    changes = {}
    for col in numeric_cols:
        prev_val = prev_row[col]
        if prev_val:
            changes[col] = round((last_row[col] - prev_val) / prev_val * 100, 1)
    return changes
