"""Reads a CSV financial report into a DataFrame and a text summary for prompts."""
import pandas as pd


def load_dataframe(filepath: str) -> pd.DataFrame:
    return pd.read_csv(filepath)


def summarize_report(filepath: str) -> str:
    df = load_dataframe(filepath)
    preview = df.head(5).to_string(index=False)
    stats = df.describe().to_string()
    return f"Data shape: {df.shape}\n\nPreview:\n{preview}\n\nStats:\n{stats}"
