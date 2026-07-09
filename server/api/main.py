"""Thin, stateless FastAPI layer.

Exactly two responsibilities per PLAN.md:
1. Serve read-only problem bank data (GET /problems, GET /problems/{slug}).
2. Mint LiveKit access tokens (POST /livekit/token).

No tutoring logic, no session state, no LangGraph, no LiveKit agent worker --
those live in graph/ and agent/ respectively and are owned elsewhere.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import api as lk_api
from pydantic import BaseModel

from problems import get_problem, list_problems
from problems.schema import (
    BruteForce,
    ComprehensionRubric,
    HintLevel,
    Loophole,
    OptimalApproach,
)

# Secrets live in the repo root .env (gitignored), not /server/.env.
# /server/api/main.py -> parents[2] is the repo root (Volna-Code/).
_ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=_ROOT_ENV)

app = FastAPI(title="DSA Tutor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# Problem bank endpoints
# --------------------------------------------------------------------------


class ProblemSummary(BaseModel):
    """Lightweight shape for the problem-selection list page."""

    slug: str
    title: str
    difficulty: str


class TestCasePublic(BaseModel):
    """A test case shape with the answer stripped out.

    Deliberately omits `expected` and `explanation_if_failed` -- see the
    reasoning on ProblemDetail below.
    """

    id: str
    args: dict[str, Any]
    is_edge_case: bool
    edge_case_tag: str | None = None


class ProblemDetail(BaseModel):
    """Full problem detail for the problem page, minus anything that would
    hand the user (or leak into their browser devtools) the answer.

    Excluded relative to the full `Problem` model:
    - `reference_solution`: this is the literal, correct solution code. The
      frontend needs the starter code to let the user write their own
      solution, never the finished one -- shipping it in an API response
      that's trivially visible in the Network tab would defeat the entire
      point of the tutor.
    - `compare_fn` / `extra_harness_helpers`: internal Piston-harness
      plumbing (how results are diffed), not problem content. Irrelevant to
      a human reading the problem and not worth exposing.
    - `test_cases[].expected` and `.explanation_if_failed`: `expected` is
      literally the correct output for that input -- for a problem like
      Two Sum, shipping every test case's expected value would let a user
      read off the answer for every case the tutor later grades against,
      including the edge cases the comprehension-check phase is
      specifically designed to make the user *discover* out loud before
      ever seeing them listed. `explanation_if_failed` is worse: it spells
      out the exact gotcha ("the array has 7 twice, if your hash map
      overwrites...") that the voice tutor is supposed to surface only
      after the user actually stumbles on it. Both stay server-side for
      the LangGraph/Piston grading loop, which imports the real `Problem`
      objects directly (no duplication, per PLAN.md).

    Everything else (hint_ladder, brute_force, optimal_approach,
    common_loopholes, comprehension_rubric) is included per the task spec
    for this endpoint. These describe the *shape* of the tutoring
    conversation rather than handing over concrete answers.
    """

    id: int
    slug: str
    title: str
    difficulty: str
    statement: str
    constraints: list[str]
    entry_point: str
    starter_code: str
    test_cases: list[TestCasePublic]
    brute_force: BruteForce
    optimal_approach: OptimalApproach
    hint_ladder: list[HintLevel]
    common_loopholes: list[Loophole]
    comprehension_rubric: ComprehensionRubric


@app.get("/problems", response_model=list[ProblemSummary])
def get_problems() -> list[ProblemSummary]:
    return [
        ProblemSummary(slug=p.slug, title=p.title, difficulty=p.difficulty)
        for p in list_problems()
    ]


@app.get("/problems/{slug}", response_model=ProblemDetail)
def get_problem_detail(slug: str) -> ProblemDetail:
    problem = get_problem(slug)
    if problem is None:
        raise HTTPException(status_code=404, detail=f"No problem with slug '{slug}'")

    return ProblemDetail(
        id=problem.id,
        slug=problem.slug,
        title=problem.title,
        difficulty=problem.difficulty,
        statement=problem.statement,
        constraints=problem.constraints,
        entry_point=problem.entry_point,
        starter_code=problem.starter_code,
        test_cases=[
            TestCasePublic(
                id=tc.id,
                args=tc.args,
                is_edge_case=tc.is_edge_case,
                edge_case_tag=tc.edge_case_tag,
            )
            for tc in problem.test_cases
        ],
        brute_force=problem.brute_force,
        optimal_approach=problem.optimal_approach,
        hint_ladder=problem.hint_ladder,
        common_loopholes=problem.common_loopholes,
        comprehension_rubric=problem.comprehension_rubric,
    )


# --------------------------------------------------------------------------
# LiveKit token minting
# --------------------------------------------------------------------------


class TokenRequest(BaseModel):
    room: str
    identity: str
    name: str | None = None


class TokenResponse(BaseModel):
    token: str


@app.post("/livekit/token", response_model=TokenResponse)
def create_livekit_token(req: TokenRequest) -> TokenResponse:
    api_key = os.environ.get("LIVEKIT_API_KEY")
    api_secret = os.environ.get("LIVEKIT_API_SECRET")
    if not api_key or not api_secret:
        raise HTTPException(
            status_code=500,
            detail="LIVEKIT_API_KEY / LIVEKIT_API_SECRET not configured",
        )

    grants = lk_api.VideoGrants(room_join=True, room=req.room)
    token = (
        lk_api.AccessToken(api_key, api_secret)
        .with_identity(req.identity)
        .with_name(req.name or req.identity)
        .with_grants(grants)
    )

    return TokenResponse(token=token.to_jwt())
