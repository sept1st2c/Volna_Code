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
    # Transient: only ever set mid-chain, within a single graph.ainvoke() call,
    # between execution_feedback_node (tests just passed) and
    # complexity_probe_node picking it up next -- never a resting phase a
    # spoken turn's entry router needs to handle.
    "COMPLEXITY_CHECK",
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
    # substantive-attempt counters, mirroring comprehension_attempts -- see
    # graph/nodes/approach.py's _MAX_APPROACH_ATTEMPTS escape hatch. Kept
    # separate per target since brute-force and optimal are graded at
    # different points in the conversation and shouldn't share a budget.
    brute_force_attempts: int
    optimal_approach_attempts: int

    # Always just the current spoken turn's raw text, never accumulated --
    # unlike `approach_transcript` (see below), which deliberately DOES
    # accumulate across fragmented turns for the "describe your approach"
    # graders. hint_node's own stuck/not-stuck judgment explicitly wants only
    # the latest turn (see its prompt's "judge from this latest turn alone"),
    # and sharing `approach_transcript` with it was a real bug caught in
    # review: once HINT_LADDER accumulation was added for
    # optimal_approach_node's benefit, hint_node silently started receiving
    # the whole multi-turn buffer instead, contradicting its own contract.
    latest_spoken_turn: str

    # Set for exactly one worker-side accumulation decision (see
    # agent/worker.py's _process_turn) whenever loophole_node or hint_node
    # just gave the student genuinely new information to react to (a new
    # edge case, or a new/escalated hint). Without this, worker.py's
    # same-phase-means-still-accumulating heuristic can't tell "one
    # utterance split by pauses" apart from "a fresh attempt responding to
    # feedback that happens to rest at the same phase string" (comprehension
    # cycles COMPREHENSION_CHECK -> COMPREHENSION_REMEDIATION -> back to
    # COMPREHENSION_CHECK; HINT_LADDER rests at the same phase across many
    # distinct hint rounds) -- both real bugs caught in review. Cleared by
    # whichever grading node next consumes the accumulated field.
    fresh_guidance_just_delivered: bool

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

    # iteration routing: tracks whether the student is failing the SAME test
    # case repeatedly across submissions (as opposed to a fresh bug each
    # time), which is a deterministic "genuinely stuck" signal on its own --
    # no LLM judgment needed. See graph/nodes/execution_feedback.py.
    last_failing_test_id: str | None
    repeat_fail_streak: int
    # Set for exactly one hint_node call when execution_feedback_node routes
    # here due to a repeat-fail streak: skips hint_node's own StuckSignal LLM
    # judgment (the repeat failure IS the stuck signal) and forces an
    # immediate hint advance, grounded in the specific failing case.
    force_hint_advance: bool
    force_hint_test_id: str | None

    # Set by optimal_approach_node for exactly one turn when the student's
    # words weren't a real attempt to describe the approach (e.g. "give me a
    # minute") -- HINT_LADDER is both "resting phase, waiting on the student"
    # and "just advanced, deliver the next hint" for this node, and the two
    # are normally told apart by whether ready_to_advance was true. A
    # non-attempt sets phase back to HINT_LADDER too (nothing was graded), so
    # without this flag build.py's conditional edge can't tell "stay put"
    # from "advance", and would wrongly chain into hint_node, overwriting
    # the student's own acknowledgment with an unsolicited hint.
    skip_hint_this_turn: bool

    # empirical complexity check (graph/nodes/complexity.py), run once all
    # tests pass and before COMPLETE is granted.
    complexity_result: dict | None

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
        brute_force_attempts=0,
        optimal_approach_attempts=0,
        hint_level=0,
        stuck_streak=0,
        hint_max_level_stuck_rounds=0,
        last_failing_test_id=None,
        repeat_fail_streak=0,
        force_hint_advance=False,
        force_hint_test_id=None,
        skip_hint_this_turn=False,
        latest_spoken_turn="",
        fresh_guidance_just_delivered=False,
        complexity_result=None,
        session_facts="",
    )
