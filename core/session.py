"""Tracks Q&A within the current interaction session (since app start, or the last
"New Session" reset) -- a bounded, resettable window that features needing recent
context (contradiction checks, session summaries) read from, instead of the full
persisted history in memory.json.
"""
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class SessionEntry:
    question: str
    agent: str
    answer: str
    audit_verdict: str = ""
    timestamp: str = ""


class Session:
    def __init__(self):
        self.entries: list[SessionEntry] = []

    def reset(self) -> None:
        self.entries = []

    def log(self, question: str, agent: str, answer: str, audit_verdict: str = "") -> None:
        self.entries.append(SessionEntry(
            question=question,
            agent=agent,
            answer=answer,
            audit_verdict=audit_verdict,
            timestamp=datetime.now(timezone.utc).isoformat(),
        ))
