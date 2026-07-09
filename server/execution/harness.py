import json

from problems.schema import Problem

RESULTS_MARKER = "===RESULTS_JSON==="

_SCAFFOLD = """import json, math

{extra_helpers}

{user_code}

{compare_fn}

def __run_case(case):
    args = case["args"]
    try:
        result = {entry_point}(**args)
    except Exception as e:
        return {{"id": case["id"], "passed": False, "error": f"{{type(e).__name__}}: {{e}}"}}
    expected = case["expected"]
    try:
        passed = bool(_compare(result, expected, args))
    except Exception as e:
        passed = False
    if passed:
        return {{"id": case["id"], "passed": True}}
    return {{"id": case["id"], "passed": False, "actual": result, "expected": expected}}

_test_cases = json.loads('''{test_cases_json}''')
_results = [__run_case(c) for c in _test_cases]
print("{marker}")
print(json.dumps(_results))
"""


def render_harness(problem: Problem, user_code: str) -> str:
    test_cases_json = json.dumps(
        [
            {"id": tc.id, "args": tc.args, "expected": tc.expected}
            for tc in problem.test_cases
        ]
    )
    return _SCAFFOLD.format(
        extra_helpers=problem.extra_harness_helpers,
        user_code=user_code,
        compare_fn=problem.compare_fn,
        entry_point=problem.entry_point,
        test_cases_json=test_cases_json,
        marker=RESULTS_MARKER,
    )


def parse_harness_output(stdout: str) -> list[dict] | None:
    if RESULTS_MARKER not in stdout:
        return None
    _, _, tail = stdout.rpartition(RESULTS_MARKER)
    try:
        return json.loads(tail.strip())
    except json.JSONDecodeError:
        return None
