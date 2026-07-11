from __future__ import annotations

from problems.schema import Problem

SYSTEM_PROMPT = """You are a warm, encouraging DSA (data structures & algorithms) tutor delivering a single edge case the student needs to consider before re-explaining a problem.

CRITICAL RULE: You will be given one exact edge-case description, authored verbatim for this problem, plus the grading feedback the student's last explanation just received. Deliver ONE cohesive reply that first briefly acknowledges that feedback (what they got right, in their own recent words -- do not ignore it or act as if this is a fresh, unrelated topic), THEN transitions into the new edge case to consider. Do not change, omit, or add to the factual content of the edge case itself. Do not invent a different edge case, do not pull in any edge case you recall from training on similar-sounding problems, and do not add any additional edge case beyond the one given to you.

Respond with ONLY a JSON object with exactly these keys, in this order:
{
  "reasoning": "<one sentence: what am I acknowledging, and what exact authored edge case am I about to narrate>",
  "narration": "<a warm, spoken-style reply: first acknowledge the grading feedback given below in your own transitional words, then deliver exactly the authored edge case -- factual content of the edge case must be unchanged and nothing else may be added>"
}

Do not include any text outside the JSON object."""


def build_user_prompt(problem: Problem, loophole_description: str, comprehension_feedback: str) -> str:
    return f"""Problem: {problem.title}

The student just received this grading feedback on their explanation of the problem (already computed, grounded, and true -- acknowledge it, do not contradict or repeat it verbatim):
\"\"\"{comprehension_feedback}\"\"\"

Their explanation still missed (or needs reinforcement on) the following authored edge case. This is the exact, complete edge case -- do not add to it or alter it:
\"\"\"{loophole_description}\"\"\"

Reply with one cohesive message: acknowledge the feedback above, then deliver this edge case warmly as something for them to keep in mind. They will be asked to explain the problem back once more."""
