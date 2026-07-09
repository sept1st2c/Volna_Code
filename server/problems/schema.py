from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class TestCase(BaseModel):
    id: str
    args: dict[str, Any]
    expected: Any
    is_edge_case: bool = False
    edge_case_tag: str | None = None
    explanation_if_failed: str | None = None


class BruteForce(BaseModel):
    description: str
    complexity: str
    why_insufficient: str


class OptimalApproach(BaseModel):
    description: str
    complexity: str


class HintLevel(BaseModel):
    level: int
    text: str


class Loophole(BaseModel):
    id: str
    description: str
    related_test_case_id: str


class ComprehensionRubric(BaseModel):
    # Must be non-empty: comprehension_node's prompt grades against this list
    # verbatim, so an empty rubric would grade against nothing.
    key_points: list[str] = Field(min_length=1)


class Problem(BaseModel):
    id: int
    slug: str
    title: str
    difficulty: Literal["Easy", "Medium", "Hard"]
    statement: str
    constraints: list[str]
    entry_point: str
    starter_code: str
    reference_solution: str
    extra_harness_helpers: str = ""
    compare_fn: str = "def _compare(result, expected, args):\n    return result == expected\n"
    test_cases: list[TestCase]
    brute_force: BruteForce
    optimal_approach: OptimalApproach
    # Must be non-empty: hints.py's hint_node computes
    # `max_level = len(hint_ladder) - 1` and always indexes
    # `hint_ladder[hint_level]` -- an empty ladder would make max_level -1
    # and raise IndexError on the very first HINT_LADDER turn.
    hint_ladder: list[HintLevel] = Field(min_length=1)
    # loophole_node already degrades gracefully for an empty list (its
    # `if next_loophole is None` branch), but a non-empty list is still
    # required content-wise -- the comprehension gate is meant to exercise at
    # least one authored edge case per problem.
    common_loopholes: list[Loophole] = Field(min_length=1)
    comprehension_rubric: ComprehensionRubric
