"""Runs evaluation/test_cases.json through the full pipeline and prints a scorecard."""
import json
import os
import time

from core.memory import Memory
from core.router import run_pipeline

TEST_CASES_FILE = os.path.join(os.path.dirname(__file__), "test_cases.json")
SCRATCH_MEMORY_FILE = "scorecard_memory.json"
PACING_SECONDS = 6  # stay under free-tier RPM limits between live LLM calls


def _missing_keywords(text: str, keywords: list[str]) -> list[str]:
    lowered = text.lower()
    return [kw for kw in keywords if kw.lower() not in lowered]


def run_scorecard(test_cases_file: str = TEST_CASES_FILE) -> float:
    with open(test_cases_file, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    memory = Memory(filepath=SCRATCH_MEMORY_FILE)
    passed = 0

    for i, case in enumerate(test_cases):
        if i > 0:
            time.sleep(PACING_SECONDS)
        result = run_pipeline(case["input"], filepath=case.get("filepath"), memory=memory)

        reasons = []
        if result.agent != case["expected_agent"]:
            reasons.append(f"routed to {result.agent}, expected {case['expected_agent']}")

        missing = _missing_keywords(result.answer, case.get("expected_keywords", []))
        if missing:
            reasons.append(f"missing keywords {missing}")

        forbidden = [kw for kw in case.get("must_not_contain", []) if kw.lower() in result.answer.lower()]
        if forbidden:
            reasons.append(f"contains forbidden keywords {forbidden}")

        ok = not reasons
        passed += ok
        mark = "PASS" if ok else "FAIL"
        detail = "" if ok else " - " + "; ".join(reasons)
        print(f"{case['id']}: {mark}{detail}")
        if not ok:
            print(f"    answer: {result.answer[:150]!r}")

    total = len(test_cases)
    score = passed / total if total else 0.0
    print(f"\nScore: {passed}/{total} ({score:.1%})")

    if os.path.exists(SCRATCH_MEMORY_FILE):
        os.remove(SCRATCH_MEMORY_FILE)

    return score


if __name__ == "__main__":
    run_scorecard()
