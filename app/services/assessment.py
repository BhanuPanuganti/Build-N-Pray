"""Safe, deterministic helpers for DSA interview assessments.

This module never executes candidate code. A deployment should additionally use
an isolated code runner for correctness tests.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import re


DSA_PROBLEMS: dict[str, dict[str, object]] = {
    "easy": {"title": "Two Sum", "prompt": "Given nums and target, return indices of two values whose sum is target.", "expected_time": "O(n)", "expected_space": "O(n)", "hints": ["Store values you have already seen.", "Look up target - value in a hash map."]},
    "medium": {"title": "Longest Substring Without Repeating Characters", "prompt": "Return the length of the longest substring with no repeated characters.", "expected_time": "O(n)", "expected_space": "O(min(n, alphabet))", "hints": ["Maintain a sliding window.", "Track each character's last index."]},
    "hard": {"title": "Merge K Sorted Lists", "prompt": "Merge k sorted linked lists into one sorted linked list.", "expected_time": "O(n log k)", "expected_space": "O(k)", "hints": ["Choose the smallest current list head.", "Use a min-heap for available heads."]},
}


def dsa_problem(difficulty: str, hint_index: int = -1) -> dict[str, object]:
    problem = DSA_PROBLEMS.get(difficulty, DSA_PROBLEMS["medium"])
    hints = problem["hints"]
    return {"difficulty": difficulty if difficulty in DSA_PROBLEMS else "medium", "title": problem["title"], "prompt": problem["prompt"], "expected_time": problem["expected_time"], "expected_space": problem["expected_space"], "hint": hints[hint_index] if 0 <= hint_index < len(hints) else None, "hints_available": len(hints)}


def _estimate_complexity(code: str) -> tuple[str, str, str]:
    text = code.lower()
    heap = any(x in text for x in ("heapq", "priorityqueue", "heappush", "priority_queue"))
    nested = bool(re.search(r"(?:for|while)\b[\s\S]{0,350}(?:for|while)\b", text))
    sorting = any(x in text for x in (".sort(", "sorted(", "arrays.sort", "collections.sort"))
    mapping = any(x in text for x in ("dict(", "{}", "hashmap", "unordered_map", "map<", "set("))
    if heap:
        time, approach = "O(n log k)", "heap-based merge"
    elif nested:
        time, approach = "O(n²)", "nested iteration"
    elif sorting:
        time, approach = "O(n log n)", "sorting-based approach"
    else:
        time, approach = "O(n)", "single-pass / hash-based approach"
    return time, ("O(n)" if mapping or heap else "O(1) auxiliary"), approach


def evaluate_dsa_submission(code: str, difficulty: str) -> dict[str, object]:
    """Return a transparent heuristic; it deliberately makes no cheating claim."""
    time, space, approach = _estimate_complexity(code)
    target = dsa_problem(difficulty)
    if not code.strip(): score = 0
    elif time == "O(n²)" and target["expected_time"] in {"O(n)", "O(n log k)"}: score = 45
    elif "heap" in approach and difficulty == "hard": score = 88
    elif time == "O(n)" and difficulty in {"easy", "medium"}: score = 85
    else: score = 70
    feedback = f"Estimated {time} time and {space} space using a {approach}."
    if time == "O(n²)" and target["expected_time"] == "O(n)": feedback += " Aim for O(n) by avoiding an inner scan."
    quality = "Run this in a sandbox against visible and hidden tests before assigning a final correctness score."
    if len(code.strip()) < 25: quality = "Submission is too short to evaluate reliably; complete edge-case handling."
    return {"score": score, "time_complexity": time, "space_complexity": space, "complexity_feedback": feedback, "code_quality_feedback": quality, "likely_approach": approach, "expected_time_complexity": target["expected_time"], "expected_space_complexity": target["expected_space"], "submitted_at": datetime.now(timezone.utc).isoformat()}
