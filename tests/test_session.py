"""core/session.py: the resettable in-session Q&A window."""
from core.session import Session


def test_new_session_has_no_entries():
    session = Session()
    assert session.entries == []


def test_log_appends_an_entry():
    session = Session()
    session.log("Which month had the highest profit?", "research", "June, at $89,000.")
    assert len(session.entries) == 1
    assert session.entries[0].agent == "research"
    assert session.entries[0].answer == "June, at $89,000."


def test_reset_clears_entries():
    session = Session()
    session.log("q1", "audit", "a1")
    session.log("q2", "research", "a2")
    session.reset()
    assert session.entries == []
