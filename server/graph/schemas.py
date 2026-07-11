from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ComprehensionGrade(BaseModel):
    reasoning: str = Field(description="Brief reasoning grounded ONLY in the rubric key points provided, before committing to a verdict.")
    is_substantive_attempt: bool = Field(description="False if the student's words are not actually an attempt to explain the problem -- a mic check, filler ('uh', 'okay'), a question, or off-topic chatter. True only if they genuinely tried to restate the problem, even if wrong or incomplete.")
    score: int = Field(ge=0, le=100)
    covered_points: list[str] = Field(description="Which of the provided key_points the user's explanation actually covered.")
    gaps: list[str] = Field(description="Which of the provided key_points the user's explanation missed or got wrong.")
    ready_to_advance: bool
    feedback_to_user: str = Field(description="Warm, spoken-style feedback naming what was covered and, if any, what to reconsider. If the student asked a direct question or asked whether they were right, answer that plainly first. Must not invent DSA facts beyond what was provided in context.")


class ApproachGrade(BaseModel):
    reasoning: str = Field(description="Brief reasoning grounded ONLY in the provided approach description, before committing to a verdict.")
    is_substantive_attempt: bool = Field(description="False if the student's words are not actually an attempt to describe an approach -- a request for time to think, a clarifying question, filler, or off-topic chatter. True only if they genuinely tried to describe how they'd solve it, even if wrong or incomplete.")
    identified_approach: Literal["brute_force", "optimal", "other", "unclear"]
    complexity_correct: bool
    matches_expected: bool
    user_seems_stuck: bool
    ready_to_advance: bool
    feedback_to_user: str = Field(description="Warm, spoken-style feedback. If the student asked a direct question, answer it first. Must not invent DSA facts beyond what was provided in context.")


class StuckSignal(BaseModel):
    reasoning: str
    user_seems_stuck: bool
    confidence: float = Field(ge=0.0, le=1.0)


class Narration(BaseModel):
    """Shared contract for narration-only nodes (no verdict, nothing for a
    conditional edge to branch on) -- loophole delivery, the coding-pause
    probe, and execution feedback. `reasoning` still comes first so the model
    grounds itself before speaking, but it is never shown to the user."""

    reasoning: str = Field(description="Brief grounding check: what authored fact/result am I about to narrate, before phrasing it warmly.")
    narration: str = Field(description="What to actually say to the user. Must not introduce any fact not present in the provided context.")
