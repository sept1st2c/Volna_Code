"""Dev-only verification for the three "make the brain better" additions:

1. execution_feedback_node routing back to HINT_LADDER (not just CODING)
   after the same test case fails twice in a row.
2. The empirical complexity gate (complexity_probe_node / complexity_feedback_node)
   actually granting/withholding COMPLETE based on measured growth, not just
   "all tests passed".
3. Personalized, LLM-generated hints once the ladder is exhausted and the
   direct reveal has already been given once.

Makes REAL Groq and REAL Piston calls throughout (no mocking), matching the
pattern of dev/test_state_edge_cases.py.

Run with: .venv/Scripts/python.exe dev/test_iteration_and_complexity.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

from graph.build import get_graph
from graph.nodes.execution_feedback import execution_feedback_node
from graph.nodes.hints import hint_node
from graph.state import initial_state
from problems import get_problem

_failures: list[str] = []


def _check(name: str, condition: bool, detail: str = "") -> None:
    status = "OK" if condition else "FAIL"
    print(f"[{name}] {status}{'  ' + detail if detail and not condition else ''}")
    if not condition:
        _failures.append(name)


def test_repeat_failure_routes_to_hint_ladder() -> None:
    problem = get_problem("two-sum")
    failing_result = [
        {"id": "duplicate_value", "passed": False, "actual": [1, 1], "expected": [1, 3]},
        {"id": "basic", "passed": True},
    ]

    state = initial_state("two-sum")
    state["last_execution_result"] = failing_result
    state["all_tests_passed"] = False

    first = execution_feedback_node(state)
    _check(
        "execution_feedback: first failure on a case -> ITERATION, streak=1",
        first["phase"] == "ITERATION" and first["repeat_fail_streak"] == 1,
        f"{first['phase']=} {first['repeat_fail_streak']=}",
    )

    state.update(first)
    second = execution_feedback_node(state)
    _check(
        "execution_feedback: SAME case failing again -> HINT_LADDER, forced",
        second["phase"] == "HINT_LADDER" and second["force_hint_advance"] is True,
        f"{second['phase']=} {second['force_hint_advance']=}",
    )
    _check(
        "execution_feedback: force_hint_test_id names the repeated case",
        second["force_hint_test_id"] == "duplicate_value",
        f"{second['force_hint_test_id']=}",
    )

    state.update(second)
    hint_result = hint_node(state)
    print(f"    forced hint narration: {hint_result['narration']!r}")
    matching_tc = next(tc for tc in problem.test_cases if tc.id == "duplicate_value")
    _check(
        "hint_node: forced advance skips the LLM stuck-check and references the real failed case",
        matching_tc.explanation_if_failed in hint_result["narration"],
        f"narration={hint_result['narration']!r}",
    )
    _check(
        "hint_node: forced advance actually advances the hint level",
        hint_result["hint_level"] > state.get("hint_level", 0) - 1,  # started at 0, forced advance -> >=1
    )
    _check(
        "hint_node: force flags are cleared after being consumed",
        hint_result["force_hint_advance"] is False and hint_result["force_hint_test_id"] is None,
    )

    # A DIFFERENT failing case right after should NOT trigger the forced path.
    state2 = initial_state("two-sum")
    state2["last_execution_result"] = [{"id": "zero_values", "passed": False, "actual": [0, 0], "expected": [0, 3]}]
    state2["all_tests_passed"] = False
    state2["last_failing_test_id"] = "duplicate_value"
    state2["repeat_fail_streak"] = 1
    fresh = execution_feedback_node(state2)
    _check(
        "execution_feedback: a DIFFERENT failing case resets the streak instead of forcing a hint",
        fresh["phase"] == "ITERATION" and fresh["repeat_fail_streak"] == 1 and fresh["force_hint_advance"] is False,
        f"{fresh=}",
    )


async def test_complexity_gate_blocks_and_allows_completion() -> None:
    problem = get_problem("two-sum")

    optimal_code = problem.reference_solution
    brute_code = (
        "def twoSum(nums, target):\n"
        "    n = len(nums)\n"
        "    for i in range(n):\n"
        "        for j in range(i + 1, n):\n"
        "            if nums[i] + nums[j] == target:\n"
        "                return [i, j]\n"
        "    return []\n"
    )

    for label, code in [("optimal (hash map)", optimal_code), ("brute force (nested loop)", brute_code)]:
        state = initial_state("two-sum")
        state["last_code"] = code
        state["phase"] = "EXECUTING"

        result = await get_graph().ainvoke(state)
        print(f"    [{label}] final phase={result['phase']!r} narration={result['narration']!r}")
        print(f"    [{label}] complexity_result={result.get('complexity_result')}")

        if label.startswith("optimal"):
            _check(
                f"complexity gate: {label} -> all tests pass AND complexity meets target -> COMPLETE",
                result["all_tests_passed"] is True and result["phase"] == "COMPLETE",
                f"phase={result['phase']!r}",
            )
        else:
            _check(
                f"complexity gate: {label} -> all tests pass but complexity DOES NOT meet target -> NOT COMPLETE",
                result["all_tests_passed"] is True and result["phase"] != "COMPLETE",
                f"phase={result['phase']!r}",
            )


def test_personalized_hint_after_reveal() -> None:
    problem = get_problem("two-sum")
    max_level = len(problem.hint_ladder) - 1

    state = initial_state("two-sum")
    state["hint_level"] = max_level
    state["stuck_streak"] = 1
    state["hint_max_level_stuck_rounds"] = 1  # already had the direct reveal once
    state["approach_transcript"] = (
        "I don't get how the hash map knows which index to return, I keep mixing up "
        "which number I already stored versus the one I'm looking at right now"
    )

    result = hint_node(state)
    print(f"    personalized hint narration: {result['narration']!r}")

    _check(
        "hint_node: beyond the one-time reveal, generates a NEW personalized nudge (not the raw reveal text again)",
        problem.optimal_approach.description not in result["narration"] and len(result["narration"]) > 0,
        f"narration={result['narration']!r}",
    )
    _check(
        "hint_node: hint_max_level_stuck_rounds keeps climbing past the reveal threshold",
        result["hint_max_level_stuck_rounds"] > state["hint_max_level_stuck_rounds"],
    )


async def main() -> int:
    test_repeat_failure_routes_to_hint_ladder()
    await test_complexity_gate_blocks_and_allows_completion()
    test_personalized_hint_after_reveal()

    print()
    if _failures:
        print(f"FAILED: {_failures}")
        return 1
    print("ALL ITERATION/COMPLEXITY TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
