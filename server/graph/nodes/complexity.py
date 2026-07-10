from __future__ import annotations

from execution.harness import parse_complexity_output, render_complexity_harness
from execution.piston import PistonError, run_python
from graph.complexity import fit_growth_exponent, meets_class
from graph.llm import generate_structured
from graph.prompts.complexity import SYSTEM_PROMPT, build_user_prompt
from graph.schemas import Narration
from graph.state import TutorState
from problems import get_problem

# The measurement harness needs real wall-clock room to time several input
# sizes in one Piston call -- well above the 3s correctness-check budget.
_COMPLEXITY_RUN_TIMEOUT_MS = 8000
_COMPLEXITY_HTTP_TIMEOUT_S = 20.0

_PASSED_FALLBACK = Narration(
    reasoning="Narration call failed after retry; falling back to a plain, factually safe success statement since both checks already passed.",
    narration="Nice -- your solution scales the way this problem asks for.",
)

_FAILED_FALLBACK = Narration(
    reasoning="Narration call failed after retry; falling back to a generic statement that names no specific (and possibly invented) exponent.",
    narration="Your code passes every test case, but it doesn't scale quite the way this problem is asking for yet -- let's tighten that up.",
)

_TIMED_OUT_FALLBACK = Narration(
    reasoning="The measurement run itself did not finish within a generous time budget across increasing input sizes -- that alone is real evidence of a scaling problem, stated without claiming a specific exponent we don't have.",
    narration=(
        "Your code passes every test case, but it didn't finish running against larger inputs within a "
        "generous time budget -- that alone suggests it isn't scaling the way this problem needs yet."
    ),
)


async def complexity_probe_node(state: TutorState) -> dict:
    """Empirically measures the submitted (already all-tests-passing) code's
    real time/space growth across increasing input sizes and classifies it
    against the problem's authored optimal complexity -- a genuine
    measurement, never an LLM guess, so a student can pass with ANY approach
    (not just the one our reference solution happens to use) as long as it
    actually scales the way the problem asks for. Never judges correctness
    itself beyond what was actually measured -- `complexity_feedback_node` is
    the only thing allowed to narrate it.
    """
    problem = get_problem(state["problem_slug"])
    probe = problem.complexity_probe
    code = state.get("last_code", "")

    if probe is None:
        # Not authored for this problem yet -- don't block completion on a
        # check that doesn't exist.
        return {"complexity_result": None, "phase": "COMPLETE"}

    source = render_complexity_harness(problem, code)
    try:
        run = await run_python(
            source,
            timeout_s=_COMPLEXITY_HTTP_TIMEOUT_S,
            run_timeout_ms=_COMPLEXITY_RUN_TIMEOUT_MS,
        )
    except PistonError:
        # Our own infra failed to measure, not the student's fault -- fail
        # open rather than block completion on a sandbox outage.
        return {"complexity_result": None, "phase": "COMPLETE"}

    measurements = parse_complexity_output(run.get("stdout", ""))
    if not measurements:
        # The run completed (no PistonError) but never printed a parseable
        # result -- the harness was killed mid-loop by Piston's own timeout
        # before finishing every size. That is itself real evidence the
        # submission doesn't scale well enough within a generous time
        # budget, not an infra hiccup -- fail the check rather than silently
        # granting COMPLETE on a measurement we never actually got to see.
        result = {
            "time_class": probe.time_class,
            "space_class": probe.space_class or probe.time_class,
            "time_ok": False,
            "space_ok": False,
            "time_exponent": None,
            "space_exponent": None,
            "measurements": [],
            "timed_out": True,
        }
        return {"complexity_result": result, "phase": "ITERATION"}

    crashed = [m for m in measurements if m.get("error")]
    if crashed:
        result = {
            "time_class": probe.time_class,
            "space_class": probe.space_class or probe.time_class,
            "time_ok": False,
            "space_ok": False,
            "time_exponent": None,
            "space_exponent": None,
            "measurements": measurements,
        }
        return {"complexity_result": result, "phase": "ITERATION"}

    time_exp = fit_growth_exponent([(m["n"], m["elapsed"]) for m in measurements])
    space_exp = fit_growth_exponent([(m["n"], m["peak_bytes"]) for m in measurements])

    time_ok = meets_class(time_exp, probe.time_class)
    space_ok = meets_class(space_exp, probe.space_class or probe.time_class)

    result = {
        "time_class": probe.time_class,
        "space_class": probe.space_class or probe.time_class,
        "time_ok": time_ok,
        "space_ok": space_ok,
        "time_exponent": time_exp,
        "space_exponent": space_exp,
        "measurements": measurements,
    }
    return {
        "complexity_result": result,
        "phase": "COMPLETE" if (time_ok and space_ok) else "ITERATION",
    }


def complexity_feedback_node(state: TutorState) -> dict:
    """Narrates the REAL, already-computed complexity_probe_node result.
    Never re-derives or second-guesses the verdict -- `phase` was already
    decided by complexity_probe_node; this only explains it."""
    complexity_result = state.get("complexity_result")
    phase = state.get("phase", "COMPLETE")

    if complexity_result is None:
        # No probe authored, or our own infra failed to measure -- already
        # routed to COMPLETE by complexity_probe_node; say nothing extra
        # misleading about complexity specifically.
        return {"narration": "Nice, all your test cases passed.", "phase": phase}

    problem = get_problem(state["problem_slug"])
    all_ok = phase == "COMPLETE"
    if all_ok:
        fallback = _PASSED_FALLBACK
    elif complexity_result.get("timed_out"):
        fallback = _TIMED_OUT_FALLBACK
    else:
        fallback = _FAILED_FALLBACK

    result = generate_structured(
        schema=Narration,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(problem, complexity_result),
        temperature=0.2,
        fallback=fallback,
    )

    return {"narration": result.narration, "phase": phase}
