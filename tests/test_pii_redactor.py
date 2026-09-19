"""tools/pii_redactor.py: regex-based PII detection and redaction."""
from tools.pii_redactor import contains_pii, redact_pii


def test_redacts_email():
    text = "Reach me at taranehkhorshidii@gmail.com about the invoice."
    assert redact_pii(text) == "Reach me at [EMAIL_REDACTED] about the invoice."


def test_redacts_phone_number():
    text = "Call me at 5391151326 tomorrow."
    assert "[PHONE_REDACTED]" in redact_pii(text)
    assert "5391151326" not in redact_pii(text)


def test_redacts_credit_card_number():
    text = "Card number 4111111111111111 was declined."
    assert "[CC_REDACTED]" in redact_pii(text)
    assert "4111111111111111" not in redact_pii(text)


def test_redacts_multiple_patterns_in_one_string():
    text = "Email a@b.com or call 5551234567."
    out = redact_pii(text)
    assert "[EMAIL_REDACTED]" in out
    assert "[PHONE_REDACTED]" in out


def test_contains_pii_true_for_email():
    assert contains_pii("contact: a@b.com") is True


def test_contains_pii_false_for_plain_text():
    assert contains_pii("Revenue grew 12% in Q2 compared to Q1.") is False


def test_redact_pii_is_a_no_op_on_clean_text():
    text = "March revenue was 48000 with a 19000 profit."
    assert redact_pii(text) == text
