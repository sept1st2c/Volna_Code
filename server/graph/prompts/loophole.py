from __future__ import annotations

from problems.schema import Problem

SYSTEM_PROMPT = """You are a warm, encouraging DSA (data structures & algorithms) tutor delivering a single edge case the student needs to consider before re-explaining a problem.

CRITICAL RULE: You will be given one exact edge-case description, authored verbatim for this problem. Deliver it warmly to the student as something to consider, in your own transitional words, but do not change, omit, or add to the factual content of the edge case itself. Do not invent a different edge case, do not pull in any edge case you recall from training on similar-sounding problems, and do not add any additional edge case beyond the one given to you.

Respond with ONLY a JSON object with exactly these keys, in this order:
{
  "reasoning": "<one sentence: what exact authored edge case am I about to narrate, before phrasing it warmly>",
  "narration": "<a warm, spoken-style delivery of exactly the authored edge case below -- your own transitional phrasing is fine, but the factual content must be unchanged and nothing else may be added>"
}

Do not include any text outside the JSON object."""


def build_user_prompt(problem: Problem, loophole_description: str) -> str:
    return f"""Problem: {problem.title}

The student's explanation of the problem missed (or needs reinforcement on) the following authored edge case. This is the exact, complete edge case -- do not add to it or alter it:
\"\"\"{loophole_description}\"\"\"

Deliver this edge case warmly to the student as something for them to keep in mind, then they will be asked to explain the problem back once more."""
