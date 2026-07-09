from problems.schema import Problem
from problems import (
    add_two_numbers,
    longest_palindrome,
    longest_substring,
    median_two_sorted_arrays,
    two_sum,
)

_ALL: list[Problem] = [
    two_sum.PROBLEM,
    add_two_numbers.PROBLEM,
    longest_substring.PROBLEM,
    median_two_sorted_arrays.PROBLEM,
    longest_palindrome.PROBLEM,
]

PROBLEMS_BY_SLUG: dict[str, Problem] = {p.slug: p for p in _ALL}


def list_problems() -> list[Problem]:
    return list(_ALL)


def get_problem(slug: str) -> Problem | None:
    return PROBLEMS_BY_SLUG.get(slug)
