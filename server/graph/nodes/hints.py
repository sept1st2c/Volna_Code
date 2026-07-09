from __future__ import annotations

from graph.llm import generate_structured
from graph.prompts.hints import SYSTEM_PROMPT, build_user_prompt
from graph.schemas import StuckSignal
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

_FALLBACK = StuckSignal(
    reasoning="Stuck-judgment call failed after retry; defaulting to user_seems_stuck=True so the ladder never silently withholds support.",
    user_seems_stuck=True,
    confidence=0.0,
)


def hint_node(state: TutorState) -> dict:
    """Judges whether the user still seems stuck at the current hint level and,
    if so for two consecutive turns, advances the hint ladder by one level.

    Only one Groq call is made here, and it is used purely for the stuck/not-
    stuck judgment (`StuckSignal`, grounded only in the user's latest spoken
    turn -- never in DSA correctness). The hint delivery narration itself is
    built deterministically in Python by concatenating a fixed lead-in with
    the verbatim `problem.hint_ladder[hint_level].text`: this is cheaper than
    a second LLM call and, more importantly, guarantees the authored hint
    content can never be paraphrased away or altered.

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

    # The user's latest turn during HINT_LADDER continues the same live
    # discussion transcript used during APPROACH_DISCUSSION -- reused here
    # rather than a dedicated field since state.py defines no separate
    # per-turn utterance field for this phase.
    user_latest_input = state.get("approach_transcript", "")

    signal = generate_structured(
        schema=StuckSignal,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(problem, hint_level, user_latest_input),
        temperature=0.2,
        fallback=_FALLBACK,
    )

    if signal.user_seems_stuck:
        stuck_streak += 1
    else:
        stuck_streak = 0

    if stuck_streak >= _STUCK_STREAK_THRESHOLD:
        if hint_level < max_level:
            hint_level += 1
            hint_max_level_stuck_rounds = 0
        else:
            # Already at the last hint and still stuck for a full cycle --
            # there's nowhere further in the ladder to escalate to.
            hint_max_level_stuck_rounds += 1
        stuck_streak = 0

    if hint_level == max_level and hint_max_level_stuck_rounds >= _MAX_HINT_REPEATS_BEFORE_REVEAL:
        narration = f"{_REVEAL_LEAD_IN}{problem.optimal_approach.description}{_REVEAL_TRAILER}"
    else:
        hint = problem.hint_ladder[hint_level]
        narration = f"{_HINT_LEAD_IN}{hint.text}"

    return {
        "hint_level": hint_level,
        "stuck_streak": stuck_streak,
        "hint_max_level_stuck_rounds": hint_max_level_stuck_rounds,
        "narration": narration,
        "phase": "HINT_LADDER",
    }
