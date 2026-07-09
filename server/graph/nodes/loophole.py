from __future__ import annotations

from graph.llm import generate_structured
from graph.prompts.loophole import SYSTEM_PROMPT, build_user_prompt
from graph.schemas import Narration
from graph.state import TutorState
from problems import get_problem

_NO_MORE_LOOPHOLES_NARRATION = "Let's have you explain it back once more."


def loophole_node(state: TutorState) -> dict:
    """Delivers the next undelivered authored edge case (loophole) to the student.

    Picks the first entry in `problem.common_loopholes` whose id is not already
    in `state["remediated_loophole_ids"]`, phrases a warm delivery of its
    (verbatim, authored) description, and sends the student back to
    COMPREHENSION_CHECK to re-explain armed with the new edge case. If every
    authored loophole has already been delivered, skips the LLM entirely and
    returns a short deterministic narration -- there is nothing left to say
    that wasn't already invented by the model.
    """
    problem = get_problem(state["problem_slug"])
    remediated_ids = state.get("remediated_loophole_ids") or []

    next_loophole = None
    for loophole in problem.common_loopholes:
        if loophole.id not in remediated_ids:
            next_loophole = loophole
            break

    if next_loophole is None:
        return {
            "narration": _NO_MORE_LOOPHOLES_NARRATION,
            "phase": "COMPREHENSION_CHECK",
        }

    fallback = Narration(
        reasoning="Delivery call failed after retry; falling back to the authored edge-case text verbatim, unstyled.",
        narration=next_loophole.description,
    )

    result = generate_structured(
        schema=Narration,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(problem, next_loophole.description),
        temperature=0.2,
        fallback=fallback,
    )

    return {
        "narration": result.narration,
        "remediated_loophole_ids": remediated_ids + [next_loophole.id],
        "phase": "COMPREHENSION_CHECK",
    }
