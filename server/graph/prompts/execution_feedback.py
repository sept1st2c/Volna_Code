from __future__ import annotations

from problems.schema import Problem

SYSTEM_PROMPT = """You are a precise DSA (data structures & algorithms) tutor explaining the result of a REAL code execution that has already been computed by an external test harness -- you did not run this code and cannot second-guess the result.

CRITICAL RULE: Do not claim tests passed or failed beyond exactly what is stated in the context given to you. Do not invent, guess, or reconstruct a reason for a failure from your own memorized knowledge of this or similar problems. If you are given an authored `explanation_if_failed` for the failing case, you MUST use it as the grounding for why this specific case matters -- do not invent a different or additional reason. If no such explanation is given, speak only to the actual/expected values (or error) provided, without speculating about the underlying cause.

Respond with ONLY a JSON object with exactly these keys, in this order:
{
  "reasoning": "<one sentence: what real, already-computed result are you about to narrate, before phrasing it warmly>",
  "narration": "<warm, spoken-style explanation of the real result. If all tests passed, celebrate briefly and factually. If a test failed, name what happened (using the actual/expected/error given) and, if provided, the authored explanation for why this case matters -- introduce no fact not present in the context.>"
}

Do not include any text outside the JSON object."""


def _select_failing_case(problem: Problem, execution_result: list[dict]) -> tuple[dict | None, object | None]:
    """Picks which failing case to narrate: prefers a failure whose matching
    authored test case is flagged `is_edge_case=True`; otherwise falls back to
    the first failure in execution order."""
    by_id = {tc.id: tc for tc in problem.test_cases}
    failures = [r for r in execution_result if not r.get("passed", False)]
    if not failures:
        return None, None

    edge_failures = [r for r in failures if by_id.get(r.get("id")) is not None and by_id[r["id"]].is_edge_case]
    chosen = edge_failures[0] if edge_failures else failures[0]
    return chosen, by_id.get(chosen.get("id"))


def _is_uniform_exception_failure(execution_result: list[dict], failures: list[dict]) -> bool:
    """True when every failing case is an EXCEPTION (not a wrong-answer
    mismatch) and they all share the exact same error string -- i.e. a
    systemic failure like a missing/misnamed entry-point function or a bug
    that blows up on every input, rather than a logic bug specific to one
    tricky input. Distinguishing this matters because an authored
    `explanation_if_failed` is written to explain why a WRONG ANSWER happens
    on a specific tricky input -- attaching it to a failure that is actually
    "the function doesn't exist at all" would misleadingly frame a systemic
    crash as if it were about that input's edge-case content."""
    if not failures or any("error" not in r for r in failures):
        return False
    errors = {r["error"] for r in failures}
    return len(errors) == 1 and len(failures) == len(execution_result)


def build_user_prompt(problem: Problem, execution_result: list[dict], all_tests_passed: bool) -> str:
    total = len(execution_result)

    if all_tests_passed:
        return f"""Problem: {problem.title}

REAL, already-computed execution result: all {total} test case(s) passed.

Narrate this real result to the student. Do not add any caveat or hedge that isn't true -- everything genuinely passed."""

    failures = [r for r in execution_result if not r.get("passed", False)]
    uniform_exception_failure = _is_uniform_exception_failure(execution_result, failures)
    failing_case, matching_test_case = _select_failing_case(problem, execution_result)

    detail_lines = [f"- id: {failing_case.get('id')}"]
    if "error" in failing_case:
        detail_lines.append(f"- an exception occurred while running the student's code: {failing_case['error']}")
    else:
        detail_lines.append(f"- actual output: {failing_case.get('actual')!r}")
        detail_lines.append(f"- expected output: {failing_case.get('expected')!r}")

    if uniform_exception_failure:
        detail_lines.append(
            f"- this exact same error occurred on ALL {total} test case(s), not just this one -- "
            "this points to something fundamental (e.g. the expected function is missing, "
            "misnamed, or crashes unconditionally), not a bug specific to this input's content"
        )

    explanation_block = ""
    # Only attach the authored `explanation_if_failed` for a genuine
    # wrong-answer mismatch, and never when the failure is a systemic
    # exception shared by every case -- that authored text explains why a
    # WRONG ANSWER happens on this specific tricky input, which doesn't apply
    # when the real story is "nothing ran at all."
    if (
        matching_test_case is not None
        and matching_test_case.explanation_if_failed
        and "error" not in failing_case
        and not uniform_exception_failure
    ):
        explanation_block = (
            "\n\nAuthored explanation for why this exact case matters (use this as your grounding, "
            "do not invent a different reason):\n"
            f"\"\"\"{matching_test_case.explanation_if_failed}\"\"\""
        )

    return f"""Problem: {problem.title}

REAL, already-computed execution result: {total} test case(s) were run and NOT all passed.

The case to focus on:
{chr(10).join(detail_lines)}
{explanation_block}

Narrate this real result to the student, explaining what happened using only the details above."""
