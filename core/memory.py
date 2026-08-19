"""Category-scoped preference memory + run history, persisted to disk.

Only the most recent MAX_INJECTED_PREFERENCES entries for a category are ever
handed to an agent's prompt, so memory can't grow unbounded inside context.
"""
import json
import os
from datetime import datetime, timezone

MEMORY_FILE = "memory.json"
MAX_INJECTED_PREFERENCES = 5

DEFAULT_MEMORY = {
    "audit_preferences": [],
    "research_preferences": [],
    "procurement_preferences": [],
    "history": [],
}


class Memory:
    def __init__(self, filepath: str = MEMORY_FILE):
        self.filepath = filepath
        self.data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {k: list(v) for k, v in DEFAULT_MEMORY.items()}

    def save(self) -> None:
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_preference(self, category: str, preference: str) -> None:
        key = f"{category}_preferences"
        self.data.setdefault(key, []).append(preference)
        self.save()

    def get_preferences(self, category: str) -> list[str]:
        key = f"{category}_preferences"
        return self.data.get(key, [])[-MAX_INJECTED_PREFERENCES:]

    def log_history(self, action: str, result: str) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "result": result[:200],
        }
        self.data["history"].append(entry)
        self.save()
