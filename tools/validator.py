"""Input validation gate. MUST run before any user input reaches an LLM call.

Checks (in order): non-empty, length cap, prompt-injection keywords, PII presence.
"""
from dataclasses import dataclass, field

from tools.pii_redactor import contains_pii

MAX_INPUT_LENGTH = 2000

INJECTION_KEYWORDS = [
    "ignore previous",
    "ignore all previous",
    "disregard previous",
    "forget instructions",
    "forget your instructions",
    "system prompt",
    "jailbreak",
    "override",
    "you are now",
    "act as",
    "developer mode",
    "reveal your prompt",
]


@dataclass
class ValidationResult:
    ok: bool
    reason: str
    flags: list[str] = field(default_factory=list)


def validate_input(user_input: str) -> ValidationResult:
    if not user_input or not user_input.strip():
        return ValidationResult(False, "Blocked: empty input.")

    if len(user_input) > MAX_INPUT_LENGTH:
        return ValidationResult(False, f"Blocked: input exceeds {MAX_INPUT_LENGTH} characters.")

    lowered = user_input.lower()
    for keyword in INJECTION_KEYWORDS:
        if keyword in lowered:
            return ValidationResult(False, f"Blocked: suspicious input detected ('{keyword}').")

    flags = ["pii_detected"] if contains_pii(user_input) else []
    return ValidationResult(True, "ok", flags)
