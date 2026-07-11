from __future__ import annotations

from graph.llm import generate_structured
from graph.prompts import personalized_hint
from graph.prompts.hints import SYSTEM_PROMPT, build_user_prompt
from graph.schemas import Narration, StuckSignal
from graph.state import TutorState
from problems import get_problem

# Anti-rushing guardrail: only advance to the next hint level once the student
# has seemed stuck for this many *consecutive* turns at the current level.
_STUCK_STREAK_THRESHOLD = 2

# Once the student is already resting at the LAST hint level (nowhere further
# to escalate to) and completes this many additional full stuck-streak cycles
# there, stop silently repeating the same final hint forever. Instead, name
# that the ladder is exhausted and reveal the authored optimal approach
# directly -- an explicit, narrated escape hatch rather than a dead end.
# Anti-hallucination note: this is not a new fact -- `problem.optimal_approach`
# is the same authored ground truth `optimal_approach_node` already grades
# the student's spoken description against, just surfaced directly instead of
# waited on. It does not touch grading: the student must still explain it
# back and `optimal_approach_node` still decides HINT_LADDER -> CODING.
_MAX_HINT_REPEATS_BEFORE_REVEAL = 1

_HINT_LEAD_IN = "Here's something to think about: "

_REVEAL_LEAD_IN = (
    "You've now seen every hint I have for this one, so let's stop circling and I'll just walk "
    "you through the intended approach directly: "
)
_REVEAL_TRAILER = " Take a moment with that, then tell me back in your own words how it would work."

_REPEAT_FAILURE_LEAD_IN = "You've hit the same issue on two submissions in a row: "

_FALLBACK = StuckSignal(
    reasoning="Stuck-judgment call failed after retry; defaulting to user_seems_stuck=True so the ladder never silently withholds support.",
    user_seems_stuck=True,
    confidence=0.0,
)

_PERSONALIZED_FALLBACK = Narration(
    reasoning="Personalized-hint call failed after retry; falling back to a generic but honest re-offer of the authored approach rather than inventing a new angle.",
    narration="Let's slow down and go back to the approach itself -- which part of it feels unclear right now?",
)


def _repeat_failure_prefix(state: TutorState) -> str:
    """Builds the lead-in naming the specific test the student just failed
    twice in a row, using the AUTHORED `explanation_if_failed` for that case
    when available (real, already-computed data -- see
    execution_feedback_node) rather than inventing a reason."""
    test_id = state.get("force_hint_test_id")
    if not test_id:
        return ""
    problem = get_problem(state["problem_slug"])
    matching = next((tc for tc in problem.test_cases if tc.id == test_id), None)
    if matching is None or not matching.explanation_if_failed:
        return "You're running into the same failure again on your last two submissions. "
    return f"{_REPEAT_FAILURE_LEAD_IN}{matching.explanation_if_failed} "


def hint_node(state: TutorState) -> dict:
    """Judges whether the user still seems stuck at the current hint level and,
    if so for two consecutive turns, advances the hint ladder by one level.

    Only one Groq call is made here in the normal path, and it is used purely
    for the stuck/not-stuck judgment (`StuckSignal`, grounded only in the
    user's latest spoken turn -- never in DSA correctness). The hint delivery
    narration itself is built deterministically in Python by concatenating a
    fixed lead-in with the verbatim `problem.hint_ladder[hint_level].text`:
    this is cheaper than a second LLM call and, more importantly, guarantees
    the authored hint content can never be paraphrased away or altered.

    Two special paths:

    - `state["force_hint_advance"]` (set by execution_feedback_node when the
      student has now failed the SAME test case on two consecutive
      submissions): skips the StuckSignal LLM call entirely -- a repeated
      identical failure already IS the stuck signal, no judgment call needed
      -- and forces an immediate hint advance, prefixed with the authored
      reason the repeated case matters.
    - Once the ladder is exhausted AND the direct reveal has already been
      given once, further stuck cycles at the max level generate a genuinely
      PERSONALIZED nudge via a bounded LLM call grounded strictly in
      `problem.optimal_approach.description` and the student's own latest
      words -- instead of repeating the same reveal text forever.

    Deciding that the user has actually found the OPTIMAL approach is
    explicitly out of scope here -- that verdict belongs to
    `optimal_approach_node` (graph/nodes/approach.py), which reads
    `state["approach_transcript"]` and owns the HINT_LADDER -> CODING
    transition. This node never exits HINT_LADDER on its own.
    """
    problem = get_problem(state["problem_slug"])
    max_level = len(problem.hint_ladder) - 1

    hint_level = state.get("hint_level", 0)
    if hint_level < 0:
        hint_level = 0
    elif hint_level > max_level:
        hint_level = max_level

    stuck_streak = state.get("stuck_streak", 0)
    hint_max_level_stuck_rounds = state.get("hint_max_level_stuck_rounds", 0)
    forced = state.get("force_hint_advance", False)

    # `latest_spoken_turn`, NOT `approach_transcript`: the latter now
    # accumulates across turns for optimal_approach_node's benefit (grading
    # a full, possibly multi-turn approach description), but this node's own
    # stuck/not-stuck judgment is explicitly about "the latest turn alone"
    # (see prompts/hints.py) -- feeding it the whole accumulated buffer was a
    # real bug caught in review, silently breaking that contract the moment
    # HINT_LADDER accumulation was added.
    user_latest_input = state.get("latest_spoken_turn", "")

    if forced:
        stuck_streak = _STUCK_STREAK_THRESHOLD
    else:
        signal = generate_structured(
            schema=StuckSignal,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(problem, hint_level, user_latest_input),
            temperature=0.2,
            fallback=_FALLBACK,
        )
        stuck_streak = stuck_streak + 1 if signal.user_seems_stuck else 0

    if stuck_streak >= _STUCK_STREAK_THRESHOLD:
        if hint_level < max_level:
            hint_level += 1
            hint_max_level_stuck_rounds = 0
        else:
            # Already at the last hint and still stuck for a full cycle --
            # there's nowhere further in the ladder to escalate to.
            hint_max_level_stuck_rounds += 1
        stuck_streak = 0

    prefix = _repeat_failure_prefix(state) if forced else ""

    if hint_level == max_level and hint_max_level_stuck_rounds > _MAX_HINT_REPEATS_BEFORE_REVEAL:
        # Ladder exhausted AND the direct reveal already happened once --
        # generate one genuinely personalized nudge instead of repeating the
        # same reveal text forever.
        personalized = generate_structured(
            schema=Narration,
            system_prompt=personalized_hint.SYSTEM_PROMPT,
            user_prompt=personalized_hint.build_user_prompt(problem, user_latest_input),
            temperature=0.3,
            fallback=_PERSONALIZED_FALLBACK,
        )
        narration = f"{prefix}{personalized.narration}"
    elif hint_level == max_level and hint_max_level_stuck_rounds >= _MAX_HINT_REPEATS_BEFORE_REVEAL:
        narration = f"{prefix}{_REVEAL_LEAD_IN}{problem.optimal_approach.description}{_REVEAL_TRAILER}"
    else:
        hint = problem.hint_ladder[hint_level]
        narration = f"{prefix}{_HINT_LEAD_IN}{hint.text}"

    return {
        "hint_level": hint_level,
        "stuck_streak": stuck_streak,
        "hint_max_level_stuck_rounds": hint_max_level_stuck_rounds,
        "narration": narration,
        "phase": "HINT_LADDER",
        "force_hint_advance": False,
        "force_hint_test_id": None,
        # Every call here gives the student some form of new guidance (a
        # hint, the direct reveal, or a personalized nudge) -- their next
        # turn is a response to THAT, not a continuation of whatever they
        # said before, even though the resting phase string doesn't change.
        # See state.py's docstring on this field for the bug this prevents.
        "fresh_guidance_just_delivered": True,
    }
