from __future__ import annotations

from graph.llm import generate_structured
from graph.prompts.approach import Target, SYSTEM_PROMPT, build_user_prompt
from graph.schemas import ApproachGrade
from graph.state import TutorState
from problems import get_problem
from problems.schema import Problem

_FALLBACK = ApproachGrade(
    reasoning="Grading call failed after retry; defaulting to not-ready and stuck so the session never silently or falsely advances.",
    identified_approach="unclear",
    complexity_correct=False,
    matches_expected=False,
    user_seems_stuck=True,
    ready_to_advance=False,
    feedback_to_user="Sorry, I had trouble processing that. Let's talk through that again -- can you walk me through your approach once more?",
)


def _grade_approach(problem: Problem, transcript: str, target: Target) -> ApproachGrade:
    """Shared Groq call for grading either the brute-force or optimal approach
    description against the relevant authored ground truth on `problem`."""
    return generate_structured(
        schema=ApproachGrade,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(problem, transcript, target),
        temperature=0.2,
        fallback=_FALLBACK,
    )


def brute_force_node(state: TutorState) -> dict:
    """Grades the user's brute-force description against `problem.brute_force`.

    Only advances to HINT_LADDER once the user genuinely understands why the
    brute force is insufficient -- a bad or vague description keeps the
    session at APPROACH_DISCUSSION so they can try again.
    """
    problem = get_problem(state["problem_slug"])
    transcript = state.get("approach_transcript", "")

    result = _grade_approach(problem, transcript, "brute_force")

    return {
        "brute_force_grade": result,
        "narration": result.feedback_to_user,
        "phase": "HINT_LADDER" if result.ready_to_advance else "APPROACH_DISCUSSION",
    }


def optimal_approach_node(state: TutorState) -> dict:
    """Grades the user's optimal-approach description against `problem.optimal_approach`.

    Only advances to CODING once the user has genuinely found the optimal
    approach -- otherwise stays in HINT_LADDER so more hints can be given.
    """
    problem = get_problem(state["problem_slug"])
    transcript = state.get("approach_transcript", "")

    result = _grade_approach(problem, transcript, "optimal")

    return {
        "optimal_grade": result,
        "narration": result.feedback_to_user,
        "phase": "CODING" if result.ready_to_advance else "HINT_LADDER",
    }
