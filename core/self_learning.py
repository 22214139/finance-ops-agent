"""Self-learning memory: tracks routing outcomes over time, surfaces recurring
keyword-to-agent patterns, and reports aggregate agent performance. Pure bookkeeping
over already-computed results (triage label, auditor verdict, parsed confidence) --
it never calls the LLM itself.
"""
import json
import os
import re
from datetime import datetime, timezone

STORAGE_FILE = "data/self_learning.json"
PATTERN_LOOKBACK = 20
PATTERN_MIN_OCCURRENCES = 5
FAILURE_STREAK_THRESHOLD = 3

DEFAULT_STATE = {
    "routing_history": [],
    "agent_performance": {},
    "learned_patterns": [],
}

_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "did", "does", "do",
    "we", "our", "us", "in", "on", "at", "to", "for", "of", "and", "or",
    "this", "that", "there", "any", "with", "from", "by", "should", "would",
    "could", "what", "which", "who", "how", "if", "it", "be", "has", "have",
}


def _keywords(question: str) -> list[str]:
    words = re.findall(r"[a-zA-Z']+", question.lower())
    return [w for w in words if len(w) > 3 and w not in _STOPWORDS]


class SelfLearning:
    def __init__(self, filepath: str = STORAGE_FILE):
        self.filepath = filepath
        self.data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "routing_history": [],
            "agent_performance": {},
            "learned_patterns": [],
        }

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.filepath) or ".", exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def record_result(self, question: str, routed_to: str, audit_verdict: str, confidence: int) -> None:
        self.data["routing_history"].append({
            "question": question,
            "routed_to": routed_to,
            "audit_verdict": audit_verdict,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        perf = self.data["agent_performance"].setdefault(
            routed_to, {"pass": 0, "fail": 0, "avg_confidence": 0}
        )
        if audit_verdict == "PASS":
            perf["pass"] += 1
        elif audit_verdict == "FAIL":
            perf["fail"] += 1
        total = perf["pass"] + perf["fail"]
        if total:
            prior_total = total - 1
            perf["avg_confidence"] = round((perf["avg_confidence"] * prior_total + confidence) / total, 1)

        self._detect_patterns()
        self._save()

    def _detect_patterns(self) -> None:
        recent = self.data["routing_history"][-PATTERN_LOOKBACK:]
        existing = {p["pattern"] for p in self.data["learned_patterns"]}

        keyword_hits: dict[tuple[str, str], int] = {}
        for entry in recent:
            if entry["audit_verdict"] != "PASS":
                continue
            for kw in _keywords(entry["question"]):
                key = (kw, entry["routed_to"])
                keyword_hits[key] = keyword_hits.get(key, 0) + 1

        for (kw, agent), count in keyword_hits.items():
            if count < PATTERN_MIN_OCCURRENCES:
                continue
            text = f"questions with '{kw}' usually go to {agent}"
            if text in existing:
                for p in self.data["learned_patterns"]:
                    if p["pattern"] == text:
                        p["occurrences"] = count
            else:
                self.data["learned_patterns"].append({
                    "pattern": text,
                    "confidence": min(99, 60 + count * 5),
                    "occurrences": count,
                })

        for agent in {e["routed_to"] for e in recent}:
            agent_entries = [e for e in recent if e["routed_to"] == agent][-FAILURE_STREAK_THRESHOLD:]
            if len(agent_entries) == FAILURE_STREAK_THRESHOLD and all(
                e["audit_verdict"] == "FAIL" for e in agent_entries
            ):
                warning = f"WARNING: {agent} has failed its last {FAILURE_STREAK_THRESHOLD} audits in a row"
                if warning not in existing:
                    self.data["learned_patterns"].append({
                        "pattern": warning,
                        "confidence": 90,
                        "occurrences": FAILURE_STREAK_THRESHOLD,
                    })

    def get_performance_report(self) -> str:
        perf = self.data["agent_performance"]
        if not perf:
            return "SYSTEM PERFORMANCE REPORT\n-------------------------\nNo routing history yet."

        lines = ["SYSTEM PERFORMANCE REPORT", "-------------------------"]
        best_agent, best_rate = None, -1.0
        worst_agent, worst_fails = None, 0
        for agent, stats in perf.items():
            total = stats["pass"] + stats["fail"]
            rate = stats["pass"] / total if total else 0.0
            lines.append(f"{agent}: {stats['pass']} PASS / {stats['fail']} FAIL ({stats['avg_confidence']}% confidence)")
            if total and rate > best_rate:
                best_agent, best_rate = agent, rate
            if stats["fail"] > worst_fails:
                worst_agent, worst_fails = agent, stats["fail"]

        if self.data["learned_patterns"]:
            lines.append("")
            lines.append("LEARNED PATTERNS:")
            for p in self.data["learned_patterns"][-10:]:
                lines.append(f"- {p['pattern']} ({p['confidence']}% confidence)")

        lines.append("")
        lines.append("RECOMMENDATIONS:")
        gave_recommendation = False
        if best_agent:
            lines.append(f"- {best_agent} performing best ({best_rate:.0%} pass rate)")
            gave_recommendation = True
        if worst_agent and worst_fails >= 2:
            lines.append(f"- {worst_agent} has {worst_fails} recent failures, consider review")
            gave_recommendation = True
        if not gave_recommendation:
            lines.append("- Not enough data yet for recommendations.")

        return "\n".join(lines)

    def get_routing_hint(self, question: str) -> str | None:
        kws = set(_keywords(question))
        best_agent, best_confidence = None, 0
        for p in self.data["learned_patterns"]:
            if p["pattern"].startswith("WARNING") or " go to " not in p["pattern"]:
                continue
            if any(f"'{kw}'" in p["pattern"] for kw in kws) and p["confidence"] > best_confidence:
                best_agent = p["pattern"].rsplit(" go to ", 1)[-1]
                best_confidence = p["confidence"]
        return best_agent
