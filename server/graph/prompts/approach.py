from __future__ import annotations

from typing import Literal

from problems.schema import Problem

Target = Literal["brute_force", "optimal"]

SYSTEM_PROMPT = """You are a patient, precise DSA (data structures & algorithms) tutor grading whether a student has correctly described an approach to solving a problem.

CRITICAL RULE: Grade solely using the approach description given to you below, which was authored specifically for this exact problem instance. Do not rely on your own memorized knowledge of "the" optimal or brute-force approach for this or any similar classic problem -- the authored description is the only ground truth, and it may differ from whatever complexity, technique, or wording you recall from training on similar-sounding problems. In particular, never override or second-guess the authored complexity or technique using outside knowledge; judge only whether the student's spoken description matches what was authored here.

Respond with ONLY a JSON object with exactly these keys, in this order:
{
  "reasoning": "<one or two sentences of grounded reasoning about how the student's description compares to the authored approach description, BEFORE committing to a verdict>",
  "identified_approach": "<one of: brute_force, optimal, other, unclear -- your best read of which approach the student is actually describing>",
  "complexity_correct": <true if the student stated (or clearly implied) a complexity matching the authored complexity given below, else false>,
  "matches_expected": <true if the student's description substantively matches the authored approach description given below, else false>,
  "user_seems_stuck": <true if the student's answer is vague, off-topic, or shows they don't have a workable approach, else false>,
  "ready_to_advance": <true only if matches_expected is true and the student shows real understanding of this specific approach, else false>,
  "feedback_to_user": "<warm, spoken-style feedback in second person. Must not introduce any DSA fact, technique, or complexity claim not already present in the authored approach description given to you.>"
}

Do not include any text outside the JSON object."""


def build_user_prompt(problem: Problem, transcript: str, target: Target) -> str:
    if target == "brute_force":
        approach_label = "brute-force"
        description = problem.brute_force.description
        complexity = problem.brute_force.complexity
        why_insufficient = problem.brute_force.why_insufficient
        authored_block = (
            f"Authored brute-force description:\n{description}\n\n"
            f"Authored brute-force complexity:\n{complexity}\n\n"
            f"Why this brute-force approach is insufficient (authored):\n{why_insufficient}"
        )
        task_instructions = (
            "The student was asked to describe a brute-force approach to this problem. "
            "Grade whether their spoken description matches the authored brute-force approach above, "
            "including whether they stated a complexity consistent with the authored complexity above."
        )
    else:
        approach_label = "optimal"
        description = problem.optimal_approach.description
        complexity = problem.optimal_approach.complexity
        authored_block = (
            f"Authored optimal-approach description:\n{description}\n\n"
            f"Authored optimal-approach complexity:\n{complexity}"
        )
        task_instructions = (
            "The student was asked to describe the optimal approach to this problem, after already "
            "discussing the brute force. Grade whether their spoken description matches the authored "
            "optimal approach above, including whether they stated a complexity consistent with the "
            "authored complexity above."
        )

    return f"""Problem: {problem.title}

{authored_block}

{task_instructions}

Here is what the student said (transcribed from speech) when asked to describe the {approach_label} approach:
\"\"\"{transcript}\"\"\"

Grade their description against the authored approach above."""
