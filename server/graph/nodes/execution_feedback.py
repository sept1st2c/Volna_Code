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


def execution_feedback_node(state: TutorState) -> dict:
    """Narrates a REAL, already-computed execution result.

    `state["last_execution_result"]` and `state["all_tests_passed"]` are
    computed elsewhere (the harness + whatever aggregates it) -- this node
    never decides pass/fail itself, it only explains the result it's handed,
    grounded in the actual failing case's `actual`/`expected`/`error` and, if
    authored, its `explanation_if_failed`.
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

    return {
        "narration": result.narration,
        "phase": "COMPLETE" if all_tests_passed else "ITERATION",
    }
