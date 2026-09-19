"""core/memory.py: category-scoped preferences + history, persisted to disk."""
from core.memory import MAX_INJECTED_PREFERENCES, Memory


def test_new_memory_file_starts_empty(tmp_path):
    mem = Memory(filepath=str(tmp_path / "memory.json"))
    assert mem.get_preferences("audit") == []


def test_add_and_get_preference(tmp_path):
    mem = Memory(filepath=str(tmp_path / "memory.json"))
    mem.add_preference("audit", "flag anything over 10% variance")
    assert mem.get_preferences("audit") == ["flag anything over 10% variance"]


def test_get_preferences_caps_at_most_recent(tmp_path):
    mem = Memory(filepath=str(tmp_path / "memory.json"))
    for i in range(MAX_INJECTED_PREFERENCES + 3):
        mem.add_preference("research", f"preference {i}")

    result = mem.get_preferences("research")
    assert len(result) == MAX_INJECTED_PREFERENCES
    # the oldest ones should have been dropped, most recent kept
    assert result[-1] == f"preference {MAX_INJECTED_PREFERENCES + 2}"


def test_preferences_persist_across_reload(tmp_path):
    path = str(tmp_path / "memory.json")
    Memory(filepath=path).add_preference("procurement", "always CC finance")

    reloaded = Memory(filepath=path)
    assert reloaded.get_preferences("procurement") == ["always CC finance"]


def test_log_history_truncates_long_results(tmp_path):
    mem = Memory(filepath=str(tmp_path / "memory.json"))
    mem.log_history("audit", "x" * 500)
    assert len(mem.data["history"][-1]["result"]) == 200
