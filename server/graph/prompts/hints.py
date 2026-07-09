from __future__ import annotations

from problems.schema import Problem

SYSTEM_PROMPT = """You are assessing whether a student learning DSA (data structures & algorithms) still seems stuck, based solely on what they just said out loud after being given a hint.

CRITICAL RULE: Judge ONLY the surface signal in the student's latest words -- are they expressing confusion, saying they have no idea, asking to just be told the answer, repeating the same question, or giving a short/empty non-answer? Or do they sound like they are actively reasoning, proposing something concrete, or asking a specific clarifying question that shows engagement with the hint? Do NOT use your own memorized knowledge of this or any DSA problem to judge whether their idea is technically correct or optimal -- that is a different job handled elsewhere. You are not grading correctness here, only whether they seem stuck or engaged.

Respond with ONLY a JSON object with exactly these keys, in this order:
{
  "reasoning": "<one sentence: what in the student's latest words made you judge them stuck or not stuck, before committing to a verdict>",
  "user_seems_stuck": <true if the student's latest turn shows confusion, no forward progress, or a request to just be told the answer; false if they show engagement or concrete reasoning>,
  "confidence": <float 0.0-1.0>
}

Do not include any text outside the JSON object."""


def build_user_prompt(problem: Problem, hint_level: int, user_latest_input: str) -> str:
    current_hint = problem.hint_ladder[hint_level].text
    return f"""Problem: {problem.title}

The student was just given the following hint (for context only -- you are not judging whether they solved the problem, only whether they still seem stuck):
\"\"\"{current_hint}\"\"\"

Here is the student's latest spoken turn:
\"\"\"{user_latest_input}\"\"\"

Judge, from this latest turn alone, whether the student still seems stuck."""
