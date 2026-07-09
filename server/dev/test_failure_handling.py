"""Dev-only regression test for failure-state hardening.

Verifies that:
  1. graph/llm.py's generate_structured() falls back safely (instead of
     raising) when the underlying Groq API call itself fails -- both a real
     network round-trip with a deliberately-broken API key (a real
     AuthenticationError from Groq's actual endpoint), and a monkeypatched
     transient failure (RateLimitError) to prove the one-retry-then-fallback
     path actually retries.
  2. execution/piston.py's run_python() converts a real network-level
     failure (nothing listening on the target port) into a PistonError
     instead of letting a raw httpx exception propagate.
  3. graph/nodes/executing.py's executing_node still produces its existing
     safe fallback dict when run_python raises for this new reason.
  4. The full graph (graph/build.py's get_graph().ainvoke) survives a
     Piston-down EXECUTING turn end-to-end with no unhandled exception.
  5. agent/worker.py's TutorAgent methods degrade safely (safe narration,
     phase reverted rather than stuck on EXECUTING) if the graph invocation
     raises despite all of the above -- the belt-and-suspenders path.

Not part of the app itself -- a verification tool, matching the pattern of
dev/test_execution.py. Run with: .venv/Scripts/python.exe dev/test_failure_handling.py

Requires network access to Groq (for the real-invalid-key test) but does
NOT require Piston to be running -- in fact the Piston-related tests point
at a deliberately-unreachable port and never touch the real sandbox.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, ".")

from dotenv import load_dotenv

# Same convention as agent/worker.py: secrets live in the repo root .env.
# server/dev/test_failure_handling.py -> parents[2] is the repo root.
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

import groq
from pydantic import BaseModel

import graph.llm as llm_mod
from graph.nodes.executing import executing_node
from graph.state import initial_state


class _Dummy(BaseModel):
    value: str


_FALLBACK = _Dummy(value="fallback")

_failures = []


def _check(name: str, condition: bool, detail: str = "") -> None:
    status = "OK" if condition else "FAIL"
    print(f"[{name}] {status}{'  ' + detail if detail and not condition else ''}")
    if not condition:
        _failures.append(name)


def test_generate_structured_hard_failure_no_retry() -> None:
    """AuthenticationError (401, not in _RETRYABLE_GROQ_ERRORS) should hit
    _call exactly once, then fall back -- no point retrying with the same
    bad credentials."""
    calls = {"n": 0}

    def _raise_auth(*a, **kw):
        calls["n"] += 1
        raise groq.AuthenticationError(
            message="invalid api key",
            response=_FakeResponse(),
            body=None,
        )

    orig_call = llm_mod._call
    llm_mod._call = _raise_auth
    try:
        result = llm_mod.generate_structured(
            schema=_Dummy,
            system_prompt="sys",
            user_prompt="user",
            fallback=_FALLBACK,
        )
    finally:
        llm_mod._call = orig_call

    _check(
        "generate_structured: hard failure (401) falls back without retry",
        result == _FALLBACK and calls["n"] == 1,
        f"result={result!r} calls={calls['n']}",
    )


def test_generate_structured_transient_failure_retries_then_succeeds() -> None:
    """RateLimitError (in _RETRYABLE_GROQ_ERRORS) should retry once; if the
    retry succeeds, the real result should be returned, NOT the fallback --
    proving the retry path is actually exercised and actually helps."""
    calls = {"n": 0}

    def _raise_then_succeed(*a, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            raise groq.RateLimitError(
                message="rate limited",
                response=_FakeResponse(status_code=429),
                body=None,
            )
        return '{"value": "recovered"}'

    orig_call = llm_mod._call
    orig_backoff = llm_mod._RETRY_BACKOFF_S
    llm_mod._call = _raise_then_succeed
    llm_mod._RETRY_BACKOFF_S = 0.01  # keep the test fast
    try:
        result = llm_mod.generate_structured(
            schema=_Dummy,
            system_prompt="sys",
            user_prompt="user",
            fallback=_FALLBACK,
        )
    finally:
        llm_mod._call = orig_call
        llm_mod._RETRY_BACKOFF_S = orig_backoff

    _check(
        "generate_structured: transient failure (429) retries and recovers",
        result == _Dummy(value="recovered") and calls["n"] == 2,
        f"result={result!r} calls={calls['n']}",
    )


def test_generate_structured_transient_failure_both_attempts_fail() -> None:
    """RateLimitError on both the initial call and the retry should still
    fall back cleanly rather than raising."""
    calls = {"n": 0}

    def _always_raise(*a, **kw):
        calls["n"] += 1
        raise groq.RateLimitError(
            message="rate limited",
            response=_FakeResponse(status_code=429),
            body=None,
        )

    orig_call = llm_mod._call
    orig_backoff = llm_mod._RETRY_BACKOFF_S
    llm_mod._call = _always_raise
    llm_mod._RETRY_BACKOFF_S = 0.01
    try:
        result = llm_mod.generate_structured(
            schema=_Dummy,
            system_prompt="sys",
            user_prompt="user",
            fallback=_FALLBACK,
        )
    finally:
        llm_mod._call = orig_call
        llm_mod._RETRY_BACKOFF_S = orig_backoff

    _check(
        "generate_structured: persistent transient failure still falls back",
        result == _FALLBACK and calls["n"] == 2,
        f"result={result!r} calls={calls['n']}",
    )


def test_generate_structured_real_invalid_api_key() -> None:
    """Real network round-trip to Groq's actual endpoint with a deliberately
    invalid API key. This is a genuine API-level failure, not a mock -- Groq
    should respond with a real 401 and groq's SDK should raise
    AuthenticationError, which generate_structured must catch and fall back
    from instead of propagating."""
    orig_key = os.environ.get("GROQ_API_KEY")
    orig_client = llm_mod._client
    os.environ["GROQ_API_KEY"] = "gsk_invalid_deliberately_broken_key_for_testing"
    llm_mod._client = None
    try:
        result = llm_mod.generate_structured(
            schema=_Dummy,
            system_prompt="You are a test.",
            user_prompt="Respond with JSON matching the schema.",
            fallback=_FALLBACK,
        )
        raised = False
    except Exception as e:  # noqa: BLE001 -- deliberately broad, this is the failure case we're checking for
        raised = True
        result = None
        print(f"    (unexpected exception: {type(e).__name__}: {e})")
    finally:
        if orig_key is not None:
            os.environ["GROQ_API_KEY"] = orig_key
        else:
            os.environ.pop("GROQ_API_KEY", None)
        llm_mod._client = orig_client

    _check(
        "generate_structured: real invalid API key falls back (no exception)",
        (not raised) and result == _FALLBACK,
    )


class _FakeResponse:
    """Minimal stand-in for httpx.Response, just enough for groq's
    APIStatusError.__init__ to consume (it reads .request and .status_code)."""

    def __init__(self, status_code: int = 401):
        self.status_code = status_code
        self.request = _FakeRequest()


class _FakeRequest:
    pass


async def test_piston_connection_refused_becomes_pistonerror() -> None:
    """Point at a port nothing is listening on. httpx.ConnectError must be
    converted to PistonError with an honest message, not propagate raw."""
    import execution.piston as piston_mod

    orig_url = piston_mod.PISTON_URL
    piston_mod.PISTON_URL = "http://127.0.0.1:1/api/v2/execute"  # port 1: nothing listens here
    try:
        try:
            await piston_mod.run_python("print('hi')", timeout_s=3.0)
            raised_piston_error = False
            raised_other = False
        except piston_mod.PistonError as e:
            raised_piston_error = True
            raised_other = False
            message = str(e)
        except Exception:
            raised_piston_error = False
            raised_other = True
    finally:
        piston_mod.PISTON_URL = orig_url

    _check(
        "piston.run_python: connection failure raises PistonError (not raw httpx exception)",
        raised_piston_error and not raised_other,
        f"message={message if raised_piston_error else '(none)'}",
    )
    if raised_piston_error:
        _check(
            "piston.run_python: PistonError message is honest about the cause",
            "reach" in message.lower() and "sandbox" in message.lower(),
            message,
        )


async def test_executing_node_survives_piston_down() -> None:
    """executing_node's existing `except PistonError` handler should catch
    this new failure mode transparently and produce its usual safe fallback
    dict -- no code changes needed in executing.py itself, this just proves
    piston.py's conversion makes that existing handler actually fire."""
    import execution.piston as piston_mod

    orig_url = piston_mod.PISTON_URL
    piston_mod.PISTON_URL = "http://127.0.0.1:1/api/v2/execute"
    try:
        state = initial_state("two-sum")
        state["last_code"] = "def solution(nums, target):\n    return []\n"
        state["phase"] = "EXECUTING"
        try:
            result = await executing_node(state)
            raised = False
        except Exception as e:
            raised = True
            result = None
            print(f"    (unexpected exception: {type(e).__name__}: {e})")
    finally:
        piston_mod.PISTON_URL = orig_url

    ok = (
        not raised
        and result is not None
        and result.get("phase") == "FEEDBACK"
        and result.get("all_tests_passed") is False
        and isinstance(result.get("last_execution_result"), list)
        and len(result["last_execution_result"]) == 1
        and result["last_execution_result"][0].get("id") == "_piston_error"
    )
    _check(
        "executing_node: Piston-down produces safe FEEDBACK fallback, no exception",
        ok,
        f"result={result!r}",
    )


async def test_full_graph_survives_piston_down() -> None:
    """End-to-end: invoke the real compiled graph with Piston unreachable.
    Confirms the whole EXECUTING -> execution_feedback chain (including a
    REAL Groq call for the failure narration -- only Piston is broken here)
    completes without raising and lands on a safe, non-COMPLETE phase."""
    import execution.piston as piston_mod
    from graph.build import get_graph

    orig_url = piston_mod.PISTON_URL
    piston_mod.PISTON_URL = "http://127.0.0.1:1/api/v2/execute"
    try:
        state = initial_state("two-sum")
        state["last_code"] = "def solution(nums, target):\n    return []\n"
        state["phase"] = "EXECUTING"
        try:
            result = await get_graph().ainvoke(state)
            raised = False
        except Exception as e:
            raised = True
            result = None
            print(f"    (unexpected exception: {type(e).__name__}: {e})")
    finally:
        piston_mod.PISTON_URL = orig_url

    ok = (
        not raised
        and result is not None
        and result.get("phase") == "ITERATION"
        and result.get("all_tests_passed") is False
        and isinstance(result.get("narration"), str)
        and len(result.get("narration", "")) > 0
    )
    _check(
        "full graph: Piston-down EXECUTING turn completes safely end-to-end",
        ok,
        f"result={result!r}",
    )


async def test_worker_belt_and_suspenders() -> None:
    """agent/worker.py's TutorAgent._process_turn and handle_code_submission
    must degrade safely if get_graph().ainvoke(...) itself raises -- a
    genuinely unexpected bug, simulated here directly by monkeypatching
    get_graph(). Confirms: no exception escapes, a safe narration is
    returned, and (critically) handle_code_submission reverts `phase` off of
    "EXECUTING" instead of leaving the student stuck in a permanent
    'still running' state."""
    import agent.worker as worker_mod

    class _FakeGraph:
        async def ainvoke(self, state):
            raise RuntimeError("simulated unexpected graph bug")

    orig_get_graph = worker_mod.get_graph
    worker_mod.get_graph = lambda: _FakeGraph()
    try:
        agent = worker_mod.TutorAgent("two-sum")
        agent.state["phase"] = "APPROACH_DISCUSSION"
        narration = await agent._process_turn("some spoken text")
        process_turn_ok = (
            narration == worker_mod._UNEXPECTED_ERROR_NARRATION
            and agent.state.get("phase") == "APPROACH_DISCUSSION"  # untouched
        )

        agent2 = worker_mod.TutorAgent("two-sum")
        agent2.state["phase"] = "CODING"
        payload = await agent2.handle_code_submission("def solution(): pass")
        submission_ok = (
            payload.get("type") == "execution_result"
            and payload.get("allPassed") is False
            and agent2.state.get("phase") == "CODING"  # reverted off EXECUTING
        )
    finally:
        worker_mod.get_graph = orig_get_graph

    _check(
        "TutorAgent._process_turn: unexpected graph exception -> safe narration, phase untouched",
        process_turn_ok,
        f"narration={narration!r} phase={agent.state.get('phase')!r}",
    )
    _check(
        "TutorAgent.handle_code_submission: unexpected graph exception -> safe payload, phase reverted off EXECUTING",
        submission_ok,
        f"payload={payload!r} phase={agent2.state.get('phase')!r}",
    )


async def main() -> int:
    test_generate_structured_hard_failure_no_retry()
    test_generate_structured_transient_failure_retries_then_succeeds()
    test_generate_structured_transient_failure_both_attempts_fail()
    test_generate_structured_real_invalid_api_key()

    await test_piston_connection_refused_becomes_pistonerror()
    await test_executing_node_survives_piston_down()
    await test_full_graph_survives_piston_down()
    await test_worker_belt_and_suspenders()

    print()
    if _failures:
        print(f"FAILED: {_failures}")
        return 1
    print("ALL FAILURE-HANDLING TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
