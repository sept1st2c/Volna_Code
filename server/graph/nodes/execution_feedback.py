from __future__ import annotations

from graph.llm import generate_structured
from graph.prompts.execution_feedback import SYSTEM_PROMPT, build_user_prompt
from graph.schemas import Narration
from graph.state import TutorState
from problems import get_problem

_PASSED_FALLBACK = Narration(
    reasoning="Narration call failed after retry; falling back to a plain, factually safe success statement since all_tests_passed was already True.",
    narration="Nice, all your test cases passed.",
)

_FAILED_FALLBACK = Narration(
    reasoning="Narration call failed after retry; falling back to a generic statement that asserts no specific (and possibly invented) reason for the failure.",
    narration="Some test cases didn't pass -- let's look at what happened.",
)

# How many consecutive submissions failing the exact same test case counts as
# "genuinely stuck, not just iterating on a fresh bug" -- deterministic, no
# LLM judgment needed, since the repeat itself is the ground-truth signal.
_REPEAT_FAIL_THRESHOLD = 2


def execution_feedback_node(state: TutorState) -> dict:
    """Narrates a REAL, already-computed execution result, then decides
    where the session goes next.

    `state["last_execution_result"]` and `state["all_tests_passed"]` are
    computed elsewhere (the harness + whatever aggregates it) -- this node
    never decides pass/fail itself, it only explains the result it's handed,
    grounded in the actual failing case's `actual`/`expected`/`error` and, if
    authored, its `explanation_if_failed`.

    Routing:
    - All tests passed -> COMPLEXITY_CHECK (chains into complexity_probe_node
      next in the same turn; that node/complexity_feedback_node decides the
      real COMPLETE verdict).
    - Failed, and this is the same test case failing for the
      `_REPEAT_FAIL_THRESHOLD`th consecutive submission -> HINT_LADDER,
      chaining directly into hint_node in this same turn (a repeated
      identical failure across submissions is deterministic evidence the
      student is stuck, not just fixing a fresh bug -- no LLM opinion
      required to make that call).
    - Otherwise -> ITERATION (back to CODING for another attempt).
    """
    problem = get_problem(state["problem_slug"])
    execution_result = state.get("last_execution_result", [])
    all_tests_passed = state.get("all_tests_passed", False)

    fallback = _PASSED_FALLBACK if all_tests_passed else _FAILED_FALLBACK

    result = generate_structured(
        schema=Narration,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(problem, execution_result, all_tests_passed),
        temperature=0.2,
        fallback=fallback,
    )

    if all_tests_passed:
        return {
            "narration": result.narration,
            "phase": "COMPLEXITY_CHECK",
            "last_failing_test_id": None,
            "repeat_fail_streak": 0,
            "force_hint_advance": False,
            "force_hint_test_id": None,
        }

    first_failure = next((r for r in execution_result if not r.get("passed")), None)
    failing_id = first_failure.get("id") if first_failure else None

    if failing_id is not None and failing_id == state.get("last_failing_test_id"):
        repeat_fail_streak = state.get("repeat_fail_streak", 0) + 1
    else:
        repeat_fail_streak = 1

    if repeat_fail_streak >= _REPEAT_FAIL_THRESHOLD:
        return {
            "narration": result.narration,
            "phase": "HINT_LADDER",
            "last_failing_test_id": failing_id,
            # Reset so the NEXT `_REPEAT_FAIL_THRESHOLD`-in-a-row (even on
            # this same case, post-hint) can trigger another hint bump.
            "repeat_fail_streak": 0,
            "force_hint_advance": True,
            "force_hint_test_id": failing_id,
        }

    return {
        "narration": result.narration,
        "phase": "ITERATION",
        "last_failing_test_id": failing_id,
        "repeat_fail_streak": repeat_fail_streak,
        "force_hint_advance": False,
        "force_hint_test_id": None,
    }
