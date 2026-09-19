"""Anomaly detection: the pure-pandas math in agents/anomaly_detection.py and
tools/anomaly_alert.py (the upload-time banner uses the exact same threshold,
so a real spike must be caught by both).
"""
import os

import pandas as pd

from agents.anomaly_detection import detect_anomalies
from tools.anomaly_alert import check_on_upload

SAMPLE_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "sample_report.csv")


def test_detects_no_anomalies_on_a_flat_series():
    df = pd.DataFrame({"month": ["Jan", "Feb", "Mar", "Apr"], "revenue": [1000, 1010, 990, 1005]})
    assert detect_anomalies(df) == []


def test_detects_an_obvious_outlier():
    # A tight cluster plus one clear outlier. (A tiny sample with an extreme single
    # outlier is a classic z-score masking case -- the outlier inflates its own std
    # enough to hide itself -- so this uses a slightly larger, realistic cluster.)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]
    revenue = [1000, 1010, 990, 1005, 995, 1002, 998, 3000]
    df = pd.DataFrame({"month": months, "revenue": revenue})
    findings = detect_anomalies(df)
    assert len(findings) == 1
    assert "revenue" in findings[0]
    assert "Aug" in findings[0]


def test_real_sample_report_flags_junes_spike():
    df = pd.read_csv(SAMPLE_CSV)
    findings = detect_anomalies(df)
    joined = " ".join(findings)
    assert "June" in joined
    assert "revenue" in joined


def test_check_on_upload_matches_detect_anomalies_threshold():
    # Same file, same threshold -- the upload banner and the audit agent must agree.
    alert_text = check_on_upload(SAMPLE_CSV)
    assert "June" in alert_text
    assert "AUTO-ALERT" in alert_text


def test_check_on_upload_handles_no_file():
    assert check_on_upload("") == ""
