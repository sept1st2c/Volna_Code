from __future__ import annotations

from execution.harness import parse_harness_output, render_harness
from execution.piston import PistonError, run_python
from graph.state import TutorState
from problems import get_problem


async def executing_node(state: TutorState) -> dict:
    """Runs the user's real code against the problem's real test cases via
    Piston. Never judges correctness itself beyond what the sandbox actually
    reports -- `all_tests_passed` and `last_execution_result` are the only
    facts `execution_feedback_node` is allowed to narrate."""
    problem = get_problem(state["problem_slug"])
    code = state.get("last_code", "")

    source = render_harness(problem, code)
    try:
        run = await run_python(source)
    except PistonError as e:
        return {
            "last_execution_result": [{"id": "_piston_error", "passed": False, "error": str(e)}],
            "all_tests_passed": False,
            "phase": "FEEDBACK",
        }

    results = parse_harness_output(run.get("stdout", ""))
    if results is None:
        stderr = run.get("stderr", "") or run.get("output", "")
        return {
            "last_execution_result": [{"id": "_run_error", "passed": False, "error": stderr or "no output produced"}],
            "all_tests_passed": False,
            "phase": "FEEDBACK",
        }

    all_passed = all(r.get("passed") for r in results)
    return {
        "last_execution_result": results,
        "all_tests_passed": all_passed,
        "phase": "FEEDBACK",
    }
