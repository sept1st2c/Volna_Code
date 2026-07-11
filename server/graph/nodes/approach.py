from __future__ import annotations

from graph.llm import generate_structured
from graph.prompts.approach import Target, SYSTEM_PROMPT, build_user_prompt
from graph.schemas import ApproachGrade
from graph.state import TutorState
from problems import get_problem
from problems.schema import Problem

_FALLBACK = ApproachGrade(
    reasoning="Grading call failed after retry; defaulting to not-ready and stuck so the session never silently or falsely advances.",
    is_substantive_attempt=False,
    identified_approach="unclear",
    complexity_correct=False,
    matches_expected=False,
    user_seems_stuck=True,
    ready_to_advance=False,
    feedback_to_user="Sorry, I had trouble processing that. Let's talk through that again -- can you walk me through your approach once more?",
)

# Escape hatch mirroring comprehension.py's _MAX_COMPREHENSION_ATTEMPTS: real
# grading (via generate_structured) is non-deterministic run-to-run, and
# without a cap a student who keeps *substantively* attempting but never
# quite lands the authored description could loop here forever. Only counts
# genuine attempts (is_substantive_attempt=True) -- asking for a moment to
# think, or a clarifying question, never burns this budget.
_MAX_APPROACH_ATTEMPTS = 5

_MOVING_ON_CAVEAT = (
    " We've been through this a good number of times, so let's move on -- we can always come back "
    "to this if it comes up again."
)


def _grade_approach(problem: Problem, transcript: str, target: Target, attempt_number: int) -> ApproachGrade:
    """Shared Groq call for grading either the brute-force or optimal approach
    description against the relevant authored ground truth on `problem`."""
    return generate_structured(
        schema=ApproachGrade,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(problem, transcript, target, attempt_number),
        temperature=0.2,
        fallback=_FALLBACK,
    )


def brute_force_node(state: TutorState) -> dict:
    """Grades the user's brute-force description against `problem.brute_force`.

    Only advances to HINT_LADDER once the user genuinely understands why the
    brute force is insufficient -- a bad or vague description keeps the
    session at APPROACH_DISCUSSION so they can try again. A request for time
    to think, or a clarifying question, doesn't count as a failed attempt and
    doesn't repeat the same pressure to describe it again (see
    ApproachGrade.is_substantive_attempt).
    """
    problem = get_problem(state["problem_slug"])
    transcript = state.get("approach_transcript", "")
    prior_attempts = state.get("brute_force_attempts", 0)

    result = _grade_approach(problem, transcript, "brute_force", prior_attempts + 1)

    # Every call at APPROACH_DISCUSSION counts toward the exhaustion budget,
    # substantive or not -- see the identical, real-testing-confirmed
    # rationale in comprehension_node. Gating the counter on
    # is_substantive_attempt let LLM classification variance silently break
    # the "guaranteed forward progress within N turns" promise the cap
    # exists to provide.
    attempts = prior_attempts + 1
    exhausted = attempts >= _MAX_APPROACH_ATTEMPTS

    if not result.is_substantive_attempt:
        phase = "HINT_LADDER" if exhausted else "APPROACH_DISCUSSION"
        narration = result.feedback_to_user + (_MOVING_ON_CAVEAT if exhausted else "")
        return {
            "brute_force_grade": result,
            "brute_force_attempts": attempts,
            "narration": narration,
            "phase": phase,
            "fresh_guidance_just_delivered": False,
        }

    if result.ready_to_advance:
        phase, narration = "HINT_LADDER", result.feedback_to_user
    elif exhausted:
        phase, narration = "HINT_LADDER", result.feedback_to_user + _MOVING_ON_CAVEAT
    else:
        phase, narration = "APPROACH_DISCUSSION", result.feedback_to_user

    return {
        "brute_force_grade": result,
        "brute_force_attempts": attempts,
        "narration": narration,
        "phase": phase,
        "fresh_guidance_just_delivered": False,
    }


def optimal_approach_node(state: TutorState) -> dict:
    """Grades the user's optimal-approach description against `problem.optimal_approach`.

    Only advances to CODING once the user has genuinely found the optimal
    approach -- otherwise stays in HINT_LADDER so more hints can be given
    (and the hint ladder's own stuck-detection continues to drive that).
    """
    problem = get_problem(state["problem_slug"])
    transcript = state.get("approach_transcript", "")
    prior_attempts = state.get("optimal_approach_attempts", 0)

    result = _grade_approach(problem, transcript, "optimal", prior_attempts + 1)

    if not result.is_substantive_attempt:
        # phase="HINT_LADDER" here means "stay resting here", not "advance" --
        # skip_hint_this_turn tells build.py's conditional edge not to chain
        # into hint_node, which would otherwise overwrite this acknowledgment
        # with an unsolicited hint (see the field's docstring in state.py).
        return {
            "optimal_grade": result,
            "narration": result.feedback_to_user,
            "phase": "HINT_LADDER",
            "skip_hint_this_turn": True,
            "fresh_guidance_just_delivered": False,
        }

    return {
        "optimal_grade": result,
        "optimal_approach_attempts": prior_attempts + 1,
        "narration": result.feedback_to_user,
        "phase": "CODING" if result.ready_to_advance else "HINT_LADDER",
        "skip_hint_this_turn": False,
        "fresh_guidance_just_delivered": False,
    }
