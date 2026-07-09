"""Dev-only script: runs every problem's reference solution through Piston
and confirms every test case (including edge cases) passes. Not part of the
app itself -- a verification tool for the problem bank + execution pipeline.

Run with: .venv/Scripts/python.exe dev/test_execution.py
"""

import asyncio
import sys

sys.path.insert(0, ".")

from execution.harness import parse_harness_output, render_harness
from execution.piston import run_python
from problems import list_problems


async def main() -> int:
    all_ok = True
    for problem in list_problems():
        source = render_harness(problem, problem.reference_solution)
        run = await run_python(source)
        stdout = run.get("stdout", "")
        stderr = run.get("stderr", "")
        results = parse_harness_output(stdout)

        if results is None:
            all_ok = False
            print(f"[{problem.slug}] FAILED TO RUN")
            print(f"  stdout: {stdout!r}")
            print(f"  stderr: {stderr!r}")
            continue

        by_id = {r["id"]: r for r in results}
        passed = sum(1 for r in results if r["passed"])
        total = len(results)
        status = "OK" if passed == total else "FAIL"
        if passed != total:
            all_ok = False
        print(f"[{problem.slug}] {status} {passed}/{total}")
        for r in results:
            if not r["passed"]:
                print(f"    case '{r['id']}' failed: {r}")

    print()
    print("ALL PROBLEMS PASSED" if all_ok else "SOME PROBLEMS FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
