"""Dev-only regression tests for the LOGIC/STATE edge-case audit of the
tutoring state machine (graph/state.py, graph/build.py, graph/nodes/*.py,
agent/worker.py). Not part of the app itself -- a verification tool, matching
the pattern of dev/test_execution.py and dev/test_failure_handling.py.

Makes REAL Groq and REAL Piston calls throughout (no mocking of the actual
services under audit) -- only the specific constant/threshold being tested is
monkeypatched, to reproduce pre-fix ("before") behavior for comparison against
the real post-fix ("after") behavior on the same code path.

Run with: .venv/Scripts/python.exe dev/test_state_edge_cases.py
"""

from __future__ import annotations

import asyncio
import math
import sys
from pathlib import Path

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

import graph.nodes.comprehension as comprehension_mod
import graph.nodes.hints as hints_mod
from graph.nodes.comprehension import comprehension_node
from graph.nodes.hints import hint_node
from graph.state import initial_state
from problems import get_problem
from problems.schema import HintLevel, Problem

_failures = []


def _check(name: str, condition: bool, detail: str = "") -> None:
    status = "OK" if condition else "FAIL"
    print(f"[{name}] {status}{'  ' + detail if detail and not condition else ''}")
    if not condition:
        _failures.append(name)


# ---------------------------------------------------------------------------
# 1. Hint ladder exhaustion -- escape hatch (graph/nodes/hints.py)
# ---------------------------------------------------------------------------


def test_hint_ladder_exhaustion() -> None:
    problem = get_problem("two-sum")
    max_level = len(problem.hint_ladder) - 1  # 3

    stuck_input = (
        "I really have no idea, I'm completely lost, can you just tell me the answer?"
    )

    # --- BEFORE: reproduce the pre-fix dead end -----------------------
    # With the reveal threshold pushed to infinity, hitting the last hint
    # level and staying stuck should behave exactly like the old code: keep
    # silently repeating the same final hint forever, with no escalation.
    orig_threshold = hints_mod._MAX_HINT_REPEATS_BEFORE_REVEAL
    hints_mod._MAX_HINT_REPEATS_BEFORE_REVEAL = math.inf
    try:
        state = initial_state("two-sum")
        state["hint_level"] = max_level
        state["stuck_streak"] = 1  # one turn away from the escalation threshold
        state["hint_max_level_stuck_rounds"] = 0
        state["approach_transcript"] = stuck_input

        before = hint_node(state)
        print(f"    (before-fix narration): {before['narration']!r}")

        expected_hint_text = problem.hint_ladder[max_level].text
        before_is_dead_end = (
            before["hint_level"] == max_level
            and expected_hint_text in before["narration"]
            and "intended approach directly" not in before["narration"]
        )
        _check(
            "hints: pre-fix behavior reproduced (repeats final hint forever, no escalation)",
            before_is_dead_end,
            f"narration={before['narration']!r}",
        )
    finally:
        hints_mod._MAX_HINT_REPEATS_BEFORE_REVEAL = orig_threshold

    # --- AFTER: the real, shipped fix ----------------------------------
    state = initial_state("two-sum")
    state["hint_level"] = max_level
    state["stuck_streak"] = 1
    state["hint_max_level_stuck_rounds"] = 0
    state["approach_transcript"] = stuck_input

    after = hint_node(state)
    print(f"    (after-fix narration): {after['narration']!r}")

    reveals_optimal_approach = (
        "intended approach directly" in after["narration"]
        and problem.optimal_approach.description in after["narration"]
    )
    _check(
        "hints: after fix, exhausting the ladder reveals the authored optimal approach",
        reveals_optimal_approach,
        f"narration={after['narration']!r}",
    )
    _check(
        "hints: phase stays HINT_LADDER (grading/advancement untouched by the reveal)",
        after["phase"] == "HINT_LADDER",
    )


# ---------------------------------------------------------------------------
# 2. Comprehension gate infinite loop -- escape hatch (graph/nodes/comprehension.py)
# ---------------------------------------------------------------------------


def test_comprehension_infinite_loop_escape_hatch() -> None:
    vague_explanation = "idk it's like some array thing, not really sure"
    n_attempts = comprehension_mod._MAX_COMPREHENSION_ATTEMPTS  # 6

    # --- BEFORE: reproduce the pre-fix infinite loop -------------------
    orig_cap = comprehension_mod._MAX_COMPREHENSION_ATTEMPTS
    comprehension_mod._MAX_COMPREHENSION_ATTEMPTS = math.inf
    try:
        state = initial_state("two-sum")
        last = None
        for i in range(n_attempts):
            state["user_explanation"] = vague_explanation
            last = comprehension_node(state)
            state.update(last)
            print(
                f"    (before-fix) attempt {i + 1}: phase={last['phase']!r} "
                f"ready_to_advance={last['comprehension_result'].ready_to_advance}"
            )
        _check(
            f"comprehension: pre-fix behavior reproduced (still stuck in REMEDIATION after {n_attempts} attempts)",
            last["phase"] == "COMPREHENSION_REMEDIATION",
            f"final phase={last['phase']!r}",
        )
    finally:
        comprehension_mod._MAX_COMPREHENSION_ATTEMPTS = orig_cap

    # --- AFTER: the real, shipped fix ----------------------------------
    state = initial_state("two-sum")
    last = None
    for i in range(n_attempts):
        state["user_explanation"] = vague_explanation
        last = comprehension_node(state)
        state.update(last)
        print(
            f"    (after-fix) attempt {i + 1}: phase={last['phase']!r} "
            f"ready_to_advance={last['comprehension_result'].ready_to_advance} "
            f"narration={last['narration']!r}"
        )

    _check(
        f"comprehension: after fix, attempt {n_attempts} advances despite a still-negative verdict",
        last["phase"] == "APPROACH_DISCUSSION"
        and last["comprehension_result"].ready_to_advance is False,
        f"final phase={last['phase']!r} ready_to_advance={last['comprehension_result'].ready_to_advance}",
    )
    _check(
        "comprehension: the override is explicitly narrated, not silent",
        "move on" in last["narration"].lower(),
        f"narration={last['narration']!r}",
    )


# ---------------------------------------------------------------------------
# 3. Concurrent code submissions -- in-flight guard (agent/worker.py)
# ---------------------------------------------------------------------------


async def test_concurrent_submission_mechanism_without_guard() -> None:
    """Reproduces the RACE MECHANISM itself (not the shipped fix): two
    coroutines racing to synchronously mutate a shared dict before an
    `await` point, mirroring exactly what `handle_code_submission`'s body
    used to do with no guard. Proves that without a guard, the first
    submission's own in-flight work can end up observing the SECOND
    submission's code -- the corruption the audit was worried about."""
    shared_state: dict = {"last_code": None, "phase": "CODING"}
    observed = {}

    async def _unguarded_submit(name: str, code: str, delay_before_read: float) -> None:
        # Exactly the old handle_code_submission body's shape: synchronous
        # mutation, then an await standing in for the real Piston round-trip.
        shared_state["last_code"] = code
        shared_state["phase"] = "EXECUTING"
        await asyncio.sleep(delay_before_read)
        # By the time this "submission" resumes and is about to act on
        # last_code (i.e. what executing_node would read), a second racing
        # submission may have already overwritten it.
        observed[name] = shared_state["last_code"]

    task_a = asyncio.create_task(_unguarded_submit("A", "CODE_A", delay_before_read=0.05))
    task_b = asyncio.create_task(_unguarded_submit("B", "CODE_B", delay_before_read=0.0))
    await asyncio.gather(task_a, task_b)

    print(f"    (unguarded mechanism) A observed last_code={observed['A']!r}, B observed last_code={observed['B']!r}")
    _check(
        "worker: unguarded mechanism reproduces cross-submission corruption (A ends up seeing B's code)",
        observed["A"] == "CODE_B",
        f"observed={observed!r}",
    )


async def test_concurrent_submission_guard_real() -> None:
    """The real, shipped fix: fires two genuinely overlapping
    `handle_code_submission` calls (real Groq narration + real Piston
    execution) at the real TutorAgent and confirms the second is rejected
    outright instead of racing with the first."""
    import agent.worker as worker_mod

    problem = get_problem("two-sum")
    good_code = problem.reference_solution
    other_code = "def twoSum(nums, target):\n    return []\n"  # deliberately wrong, easy to distinguish

    agent = worker_mod.TutorAgent("two-sum")
    agent.state["phase"] = "CODING"

    task1 = asyncio.create_task(agent.handle_code_submission(good_code))
    task2 = asyncio.create_task(agent.handle_code_submission(other_code))
    result1, result2 = await asyncio.gather(task1, task2)

    print(f"    (guarded) submission 1 (correct code): allPassed={result1['allPassed']}")
    print(f"    (guarded) submission 2 (concurrent, should be rejected): {result2}")

    second_rejected = (
        result2["allPassed"] is False
        and any(c["id"] == "_worker_error" for c in result2["cases"])
        and "still running" in (result2["cases"][0]["message"] or "").lower()
    )
    _check(
        "worker: overlapping submission is rejected, not raced",
        second_rejected,
        f"result2={result2!r}",
    )
    _check(
        "worker: the first (non-overlapping-at-guard-time) submission still completes correctly against ITS OWN code",
        result1["allPassed"] is True and agent.state.get("last_code") == good_code,
        f"result1={result1!r} agent.state['last_code']={agent.state.get('last_code')!r}",
    )
    _check(
        "worker: in-flight flag is released after completion (not stuck permanently rejecting)",
        agent._code_submission_in_flight is False,
    )


# ---------------------------------------------------------------------------
# 5. Problem data validation gap (problems/schema.py)
# ---------------------------------------------------------------------------


def test_empty_hint_ladder_validation() -> None:
    base_kwargs = get_problem("two-sum").model_dump()
    base_kwargs["hint_ladder"] = []

    # --- BEFORE: simulate the old, unvalidated schema -------------------
    # `model_construct` bypasses Pydantic validation entirely (this is what
    # the OLD schema effectively allowed for ANY hint_ladder value, since it
    # had no min_length constraint) so we can prove the runtime crash this
    # would have caused in hint_node -- a real IndexError, not theoretical.
    bad_problem = Problem.model_construct(**base_kwargs)
    _check(
        "schema: (setup) bad_problem really has an empty hint_ladder",
        bad_problem.hint_ladder == [],
    )

    state = initial_state("two-sum")
    state["hint_level"] = 0
    state["approach_transcript"] = "still stuck"

    import graph.nodes.hints as h

    orig_get_problem = h.get_problem
    h.get_problem = lambda slug: bad_problem
    crashed = False
    try:
        try:
            h.hint_node(state)
        except IndexError as e:
            crashed = True
            print(f"    (before-fix) hint_node crashed as expected: IndexError: {e}")
    finally:
        h.get_problem = orig_get_problem

    _check(
        "schema: pre-fix behavior reproduced (empty hint_ladder crashes hint_node with IndexError)",
        crashed,
    )

    # --- AFTER: the real, shipped fix ------------------------------------
    validation_rejected = False
    try:
        Problem(**base_kwargs)
    except Exception as e:  # pydantic.ValidationError
        validation_rejected = True
        print(f"    (after-fix) Problem(...) construction rejected empty hint_ladder: {type(e).__name__}")

    _check(
        "schema: after fix, an empty hint_ladder is rejected at problem-authoring time, not at runtime",
        validation_rejected,
    )


async def test_empty_and_missing_entry_point_code() -> None:
    """Item 6 audit check (no code change expected -- just confirming real
    behavior): does completely empty code, or code that never defines the
    expected entry_point at all, produce a clean PER-TEST-CASE error (caught
    inside the harness's `__run_case` try/except) rather than a harness-level
    crash that wipes out every test case with an unhelpful message? Uses the
    real Piston sandbox and the real execution_feedback narration call."""
    from graph.nodes.executing import executing_node
    from graph.nodes.execution_feedback import execution_feedback_node

    problem = get_problem("two-sum")

    for label, code in [
        ("completely empty code", ""),
        ("code defining the wrong function name", "def notTwoSum(nums, target):\n    return [0, 1]\n"),
    ]:
        state = initial_state("two-sum")
        state["last_code"] = code
        state["phase"] = "EXECUTING"

        exec_result = await executing_node(state)
        state.update(exec_result)
        results = exec_result["last_execution_result"]

        all_name_errors = results and all(
            (not r.get("passed")) and "NameError" in r.get("error", "") for r in results
        )
        _check(
            f"executing_node: {label} -> per-test-case NameError for every case (harness itself doesn't crash)",
            bool(all_name_errors) and len(results) == len(problem.test_cases),
            f"{len(results)} results, sample={results[0] if results else None}",
        )

        feedback = execution_feedback_node(state)
        _check(
            f"execution_feedback_node: {label} -> produces non-empty honest narration, no exception",
            isinstance(feedback["narration"], str) and len(feedback["narration"]) > 0,
            f"narration={feedback.get('narration')!r}",
        )
        print(f"    ({label}) narration: {feedback['narration']!r}")


async def main() -> int:
    test_hint_ladder_exhaustion()
    test_comprehension_infinite_loop_escape_hatch()
    await test_concurrent_submission_mechanism_without_guard()
    await test_concurrent_submission_guard_real()
    test_empty_hint_ladder_validation()
    await test_empty_and_missing_entry_point_code()

    print()
    if _failures:
        print(f"FAILED: {_failures}")
        return 1
    print("ALL STATE EDGE-CASE TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
