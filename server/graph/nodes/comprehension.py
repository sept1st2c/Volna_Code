from __future__ import annotations

from graph.llm import generate_structured
from graph.prompts.comprehension import SYSTEM_PROMPT, build_user_prompt
from graph.schemas import ComprehensionGrade
from graph.state import TutorState
from problems import get_problem

# Escape hatch: comprehension_node <-> loophole_node can otherwise cycle
# forever if the LLM grader never returns ready_to_advance=True (grading is
# non-deterministic run-to-run; genuinely correct explanations have been
# observed taking 3-4 tries in real testing). Once total attempts at THIS
# problem's comprehension check reach this cap, advance to
# APPROACH_DISCUSSION regardless of the verdict, with an explicit, honest
# narrated caveat -- never silently lower the grading bar (the verdict
# itself, `covered_points`/`gaps`/`ready_to_advance`, is untouched; only the
# phase transition is overridden, and the override is always spoken aloud).
# Set comfortably above the observed 3-4-try non-determinism so genuine
# back-and-forth remediation is never cut short.
_MAX_COMPREHENSION_ATTEMPTS = 6

_MOVING_ON_CAVEAT = (
    " We've gone over this problem a good number of times now, so let's move on to talk through "
    "an approach -- we can always circle back to this if it comes up again."
)

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

    attempts = state.get("comprehension_attempts", 0) + 1
    exhausted = attempts >= _MAX_COMPREHENSION_ATTEMPTS

    if result.ready_to_advance:
        phase = "APPROACH_DISCUSSION"
        narration = result.feedback_to_user
    elif exhausted:
        # Honest, narrated escape hatch -- the grader still says not ready,
        # but we advance anyway rather than trap the student here forever.
        phase = "APPROACH_DISCUSSION"
        narration = result.feedback_to_user + _MOVING_ON_CAVEAT
    else:
        phase = "COMPREHENSION_REMEDIATION"
        narration = result.feedback_to_user

    return {
        "comprehension_result": result,
        "comprehension_attempts": attempts,
        "narration": narration,
        "phase": phase,
    }
