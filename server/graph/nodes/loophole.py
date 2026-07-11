from __future__ import annotations

from graph.llm import generate_structured
from graph.prompts.loophole import SYSTEM_PROMPT, build_user_prompt
from graph.schemas import Narration
from graph.state import TutorState
from problems import get_problem

_NO_MORE_LOOPHOLES_TAIL = " Let's have you explain it back once more."


def loophole_node(state: TutorState) -> dict:
    """Delivers the next undelivered authored edge case (loophole) to the student.

    Picks the first entry in `problem.common_loopholes` whose id is not already
    in `state["remediated_loophole_ids"]`, phrases a warm delivery of its
    (verbatim, authored) description, and sends the student back to
    COMPREHENSION_CHECK to re-explain armed with the new edge case. If every
    authored loophole has already been delivered, skips the LLM entirely and
    returns a short deterministic narration -- there is nothing left to say
    that wasn't already invented by the model.

    Always leads with `comprehension_node`'s own grading feedback (already
    computed this same turn, grounded, and true) before the edge case --
    `_after_comprehension` chains straight here without ever giving the user
    a chance to hear that feedback on its own, so if this node's narration
    didn't carry it forward it would simply vanish, leaving a cold, seemingly
    unrelated edge case as the only reply to whatever the student just said.
    """
    problem = get_problem(state["problem_slug"])
    remediated_ids = state.get("remediated_loophole_ids") or []
    comprehension_result = state.get("comprehension_result")
    comprehension_feedback = comprehension_result.feedback_to_user if comprehension_result else ""

    next_loophole = None
    for loophole in problem.common_loopholes:
        if loophole.id not in remediated_ids:
            next_loophole = loophole
            break

    if next_loophole is None:
        narration = comprehension_feedback + _NO_MORE_LOOPHOLES_TAIL if comprehension_feedback else _NO_MORE_LOOPHOLES_TAIL.strip()
        return {
            "narration": narration,
            "phase": "COMPREHENSION_CHECK",
            # Tells worker.py's accumulation logic that the student is about
            # to respond to something new, even though the resting phase
            # string is unchanged (COMPREHENSION_CHECK both before and
            # after) -- see state.py's docstring on this field.
            "fresh_guidance_just_delivered": True,
        }

    fallback = Narration(
        reasoning="Delivery call failed after retry; falling back to the comprehension feedback plus the authored edge-case text verbatim, unstyled.",
        narration=f"{comprehension_feedback} {next_loophole.description}".strip(),
    )

    result = generate_structured(
        schema=Narration,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(problem, next_loophole.description, comprehension_feedback),
        temperature=0.2,
        fallback=fallback,
    )

    return {
        "narration": result.narration,
        "remediated_loophole_ids": remediated_ids + [next_loophole.id],
        "phase": "COMPREHENSION_CHECK",
        "fresh_guidance_just_delivered": True,
    }
