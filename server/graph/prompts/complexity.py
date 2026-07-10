from __future__ import annotations

from graph.complexity import describe_class
from problems.schema import Problem

SYSTEM_PROMPT = """You are a precise DSA (data structures & algorithms) tutor explaining the result of a REAL, already-computed empirical complexity measurement -- the student's own submitted code was actually timed and memory-profiled at several increasing input sizes by an external harness. You did not run this code and cannot second-guess the measurement.

CRITICAL RULE: Do not claim a growth rate, exponent, or verdict beyond exactly what is stated in the context given to you. Do not invent, guess, or reconstruct a reason from your own memorized knowledge of this or a similar problem's typical solutions. The student may have used a completely different technique than our reference solution -- judge only the measured numbers you are given, never assume which algorithm they used.

Respond with ONLY a JSON object with exactly these keys, in this order:
{
  "reasoning": "<one sentence: what real, already-measured growth result are you about to narrate, before phrasing it warmly>",
  "narration": "<warm, spoken-style explanation. If the measured growth met the target, congratulate briefly and factually -- their approach (whatever it was) actually scales the way this problem asks for. If it did not, name the mismatch using the measured numbers given, and if the code crashed on a larger generated input despite passing the given test cases, name that using the real error text provided -- introduce no fact not present in the context.>"
}

Do not include any text outside the JSON object."""


def build_user_prompt(problem: Problem, complexity_result: dict) -> str:
    target_time = complexity_result["time_class"]
    target_space = complexity_result["space_class"]
    time_ok = complexity_result["time_ok"]
    space_ok = complexity_result["space_ok"]
    time_exp = complexity_result.get("time_exponent")
    space_exp = complexity_result.get("space_exponent")
    measurements = complexity_result.get("measurements", [])

    crash = next((m for m in measurements if m.get("error")), None)

    lines = [f"Problem: {problem.title}", ""]
    lines.append(
        f"Authored target for this problem: {describe_class(target_time)} time, "
        f"{describe_class(target_space)} space (see problem.optimal_approach for the full authored description: "
        f"\"{problem.optimal_approach.description}\")."
    )
    lines.append("")

    if complexity_result.get("timed_out"):
        lines.append(
            "REAL, already-computed result: the student's code passed every given test case, but the "
            "measurement run (which times the submission at several increasing input sizes) did not finish "
            "within a generous time budget. No specific growth exponent was recovered."
        )
        return "\n".join(lines) + (
            "\n\nNarrate this real result: the code is correct but did not finish scaling up within a generous "
            "time budget, without naming a specific exponent you don't actually have."
        )

    if crash is not None:
        lines.append(
            f"REAL, already-computed result: the student's code passed every given test case, but raised an "
            f"exception on a larger generated input (size {crash['n']}) that the harness used purely to measure "
            f"scaling: {crash['error']}"
        )
        return "\n".join(lines) + "\n\nNarrate this real result, naming the crash using only the details above."

    lines.append(
        f"REAL, already-measured result: run at input sizes {[m['n'] for m in measurements]}, "
        f"observed time growth exponent ~= {time_exp:.2f} (target: {describe_class(target_time)}), "
        f"observed space growth exponent ~= {space_exp:.2f} (target: {describe_class(target_space)})."
    )
    lines.append(f"Time check: {'met' if time_ok else 'NOT met'}. Space check: {'met' if space_ok else 'NOT met'}.")

    if time_ok and space_ok:
        lines.append("\nBoth checks passed. Narrate this real success.")
    else:
        lines.append(
            "\nAt least one check failed. Narrate this real result, naming which one(s) missed the target and "
            "by roughly how much, using only the numbers above -- do not guess which specific algorithm they used."
        )

    return "\n".join(lines)
