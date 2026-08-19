"""Renders a line chart of a report's numeric columns over its label column."""
import os
import uuid

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from tools.csv_reader import load_dataframe

CHART_DIR = "data/charts"


def generate_chart(filepath: str, output_dir: str = CHART_DIR) -> str:
    df = load_dataframe(filepath)
    label_col = next((c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])), None)
    numeric_cols = df.select_dtypes(include="number").columns

    os.makedirs(output_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    x = df[label_col] if label_col else df.index
    for col in numeric_cols:
        ax.plot(x, df[col], marker="o", label=col)
    ax.set_xlabel(label_col or "index")
    ax.set_ylabel("value")
    ax.set_title("Financial report trend")
    ax.legend()
    fig.tight_layout()

    out_path = os.path.join(output_dir, f"chart_{uuid.uuid4().hex[:8]}.png")
    fig.savefig(out_path)
    plt.close(fig)
    return out_path
