from __future__ import annotations

from graph.llm import generate_structured
from graph.prompts.comprehension import SYSTEM_PROMPT, build_user_prompt
from graph.schemas import ComprehensionGrade
from graph.state import TutorState
from problems import get_problem

_FALLBACK = ComprehensionGrade(
    reasoning="Grading call failed after retry; defaulting to not-ready so the session never silently skips ahead.",
    score=0,
    covered_points=[],
    gaps=[],
    ready_to_advance=False,
    feedback_to_user="Sorry, I had trouble processing that. Could you walk me through the problem again in your own words?",
)


def comprehension_node(state: TutorState) -> dict:
    """Grades the user's restatement of the problem against the authored rubric.

    Never asserts a DSA fact itself -- `ready_to_advance` and `gaps` are the
    only things the graph's conditional edge reads to decide whether to loop
    back into remediation or advance to APPROACH_DISCUSSION.
    """
    problem = get_problem(state["problem_slug"])
    user_explanation = state.get("user_explanation", "")

    result = generate_structured(
        schema=ComprehensionGrade,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(problem, user_explanation),
        temperature=0.2,
        fallback=_FALLBACK,
    )

    return {
        "comprehension_result": result,
        "comprehension_attempts": state.get("comprehension_attempts", 0) + 1,
        "narration": result.feedback_to_user,
        "phase": "APPROACH_DISCUSSION" if result.ready_to_advance else "COMPREHENSION_REMEDIATION",
    }
