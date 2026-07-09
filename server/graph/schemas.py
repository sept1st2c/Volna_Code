from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ComprehensionGrade(BaseModel):
    reasoning: str = Field(description="Brief reasoning grounded ONLY in the rubric key points provided, before committing to a verdict.")
    score: int = Field(ge=0, le=100)
    covered_points: list[str] = Field(description="Which of the provided key_points the user's explanation actually covered.")
    gaps: list[str] = Field(description="Which of the provided key_points the user's explanation missed or got wrong.")
    ready_to_advance: bool


class ApproachGrade(BaseModel):
    reasoning: str = Field(description="Brief reasoning grounded ONLY in the provided approach description, before committing to a verdict.")
    identified_approach: Literal["brute_force", "optimal", "other", "unclear"]
    complexity_correct: bool
    matches_expected: bool
    user_seems_stuck: bool
    ready_to_advance: bool
    feedback_to_user: str = Field(description="Warm, spoken-style feedback. Must not invent DSA facts beyond what was provided in context.")


class StuckSignal(BaseModel):
    reasoning: str
    user_seems_stuck: bool
    confidence: float = Field(ge=0.0, le=1.0)
