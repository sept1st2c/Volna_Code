from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


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
    key_points: list[str]


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
    hint_ladder: list[HintLevel]
    common_loopholes: list[Loophole]
    comprehension_rubric: ComprehensionRubric
