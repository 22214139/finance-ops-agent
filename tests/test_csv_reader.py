"""tools/csv_reader.py against the project's own sample report."""
import os

from tools.csv_reader import load_dataframe, summarize_report

SAMPLE_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "sample_report.csv")


def test_load_dataframe_has_expected_shape_and_columns():
    df = load_dataframe(SAMPLE_CSV)
    assert df.shape == (6, 4)
    assert list(df.columns) == ["month", "revenue", "expenses", "profit"]


def test_summarize_report_includes_shape_and_stats():
    summary = summarize_report(SAMPLE_CSV)
    assert "Data shape: (6, 4)" in summary
    assert "Preview:" in summary
    assert "Stats:" in summary
    assert "January" in summary
