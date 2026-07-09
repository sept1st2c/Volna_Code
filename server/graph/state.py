from __future__ import annotations

from typing import Literal, TypedDict

from graph.schemas import ApproachGrade, ComprehensionGrade

Phase = Literal[
    "INTRO",
    "COMPREHENSION_CHECK",
    "COMPREHENSION_REMEDIATION",
    "APPROACH_DISCUSSION",
    "BRUTE_FORCE_ANALYSIS",
    "HINT_LADDER",
    "CODING",
    "EXECUTING",
    "FEEDBACK",
    "ITERATION",
    "COMPLETE",
]


class TutorState(TypedDict, total=False):
    """Single source of truth for one tutoring session (one room, one problem).

    Every LLM node reads authored ground truth out of the Problem object
    (looked up by problem_slug) plus the relevant slice of this state, and
    writes back only structured fields plus `narration` -- the text to speak
    next. No node is allowed to invent facts; grading verdicts drive `phase`
    transitions via the graph's conditional edges, never free text.
    """

    problem_slug: str
    phase: Phase

    # comprehension
    user_explanation: str
    comprehension_result: ComprehensionGrade
    comprehension_attempts: int
    remediated_loophole_ids: list[str]

    # approach (brute force then optimal)
    approach_transcript: str
    brute_force_grade: ApproachGrade
    optimal_grade: ApproachGrade

    # hint ladder
    hint_level: int
    stuck_streak: int
    # counts full "stuck for _STUCK_STREAK_THRESHOLD consecutive turns" cycles
    # completed while already resting at the final hint level -- i.e. cycles
    # that could no longer advance hint_level because there is no next level.
    # Once this crosses hints.py's _MAX_HINT_REPEATS_BEFORE_REVEAL, hint_node
    # stops repeating the same final hint and instead reveals the authored
    # optimal approach directly (see hints.py for the full rationale).
    hint_max_level_stuck_rounds: int

    # coding + execution
    last_code: str
    last_execution_result: list[dict]
    all_tests_passed: bool

    # narration output of the most recently run node -- what the TTS layer speaks
    narration: str

    # compact rolling summary fed into every node instead of the full transcript
    session_facts: str


def initial_state(problem_slug: str) -> TutorState:
    return TutorState(
        problem_slug=problem_slug,
        phase="INTRO",
        comprehension_attempts=0,
        remediated_loophole_ids=[],
        hint_level=0,
        stuck_streak=0,
        hint_max_level_stuck_rounds=0,
        session_facts="",
    )
