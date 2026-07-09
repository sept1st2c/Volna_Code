from __future__ import annotations

from graph.llm import generate_structured
from graph.prompts.coding_pause import SYSTEM_PROMPT, build_user_prompt
from graph.schemas import Narration
from graph.state import TutorState
from problems import get_problem

_FALLBACK = Narration(
    reasoning="Probe call failed after retry; falling back to a generic but honest check-in that asserts nothing specific about the code.",
    narration="Take your time. What are you thinking through in your code right now?",
)


def coding_pause_node(state: TutorState) -> dict:
    """Periodically probes the student with a question grounded in their
    actual in-progress code (`state["last_code"]`), never a generic or
    invented question. This is a side question during CODING, not a phase
    transition -- `phase` always stays "CODING" regardless of the answer.
    """
    problem = get_problem(state["problem_slug"])
    code = state.get("last_code", "")

    result = generate_structured(
        schema=Narration,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(problem, code),
        temperature=0.2,
        fallback=_FALLBACK,
    )

    return {
        "narration": result.narration,
        "phase": "CODING",
    }
