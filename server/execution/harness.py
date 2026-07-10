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


COMPLEXITY_MARKER = "===COMPLEXITY_JSON==="

# Times and memory-profiles the student's own submitted code across a
# handful of increasing input sizes, in ONE Piston call (same "one call per
# submission" principle as the correctness harness above). `tracemalloc`
# gives an in-process, per-size peak-allocation reading (via `reset_peak`)
# without needing to fork a subprocess per size. Never compares output
# against an expected value -- this only measures real growth, see
# graph/complexity.py for how that measurement is judged.
_COMPLEXITY_SCAFFOLD = """import json, time, tracemalloc

{extra_helpers}

{user_code}

{arg_generator}

tracemalloc.start()
_measurements = []
for _n in {sizes}:
    _args = _generate_complexity_args(_n)
    # `reset_peak()` resets the peak tracker to the CURRENT traced size, not
    # to zero -- the input args (which scale with n) are already "current" at
    # this point, so the peak read afterward would otherwise be dominated by
    # input size, not by what the algorithm itself allocates. Capture that
    # baseline explicitly and subtract it out below.
    _baseline, _ = tracemalloc.get_traced_memory()
    tracemalloc.reset_peak()
    _t0 = time.perf_counter()
    _error = None
    try:
        {entry_point}(**_args)
    except Exception as e:
        _error = f"{{type(e).__name__}}: {{e}}"
    _elapsed = time.perf_counter() - _t0
    _, _peak = tracemalloc.get_traced_memory()
    _measurements.append({{"n": _n, "elapsed": _elapsed, "peak_bytes": max(0, _peak - _baseline), "error": _error}})
print("{marker}")
print(json.dumps(_measurements))
"""


def render_complexity_harness(problem: Problem, user_code: str) -> str:
    probe = problem.complexity_probe
    assert probe is not None, "render_complexity_harness requires problem.complexity_probe"
    return _COMPLEXITY_SCAFFOLD.format(
        extra_helpers=problem.extra_harness_helpers,
        user_code=user_code,
        arg_generator=probe.arg_generator,
        sizes=json.dumps(probe.sizes),
        entry_point=problem.entry_point,
        marker=COMPLEXITY_MARKER,
    )


def parse_complexity_output(stdout: str) -> list[dict] | None:
    if COMPLEXITY_MARKER not in stdout:
        return None
    _, _, tail = stdout.rpartition(COMPLEXITY_MARKER)
    try:
        return json.loads(tail.strip())
    except json.JSONDecodeError:
        return None
