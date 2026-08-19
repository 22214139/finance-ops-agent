"""Detects and redacts common PII patterns (credit card, email, phone)."""
import re

CREDIT_CARD_RE = re.compile(r"\b\d{13,16}\b")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"\b\d{10,11}\b")

_PATTERNS = (
    (CREDIT_CARD_RE, "[CC_REDACTED]"),
    (EMAIL_RE, "[EMAIL_REDACTED]"),
    (PHONE_RE, "[PHONE_REDACTED]"),
)


def redact_pii(text: str) -> str:
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def contains_pii(text: str) -> bool:
    return any(pattern.search(text) for pattern, _ in _PATTERNS)
