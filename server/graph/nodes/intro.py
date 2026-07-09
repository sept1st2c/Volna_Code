from __future__ import annotations

from graph.state import TutorState
from problems import get_problem


def intro_node(state: TutorState) -> dict:
    """Presents the problem statement verbatim -- no LLM call, nothing to
    hallucinate. Always advances straight to COMPREHENSION_CHECK and waits
    for the student's restatement."""
    problem = get_problem(state["problem_slug"])
    narration = (
        f"Let's work through {problem.title}. {problem.statement} "
        "Go ahead and explain the problem back to me in your own words."
    )
    return {
        "narration": narration,
        "phase": "COMPREHENSION_CHECK",
    }
