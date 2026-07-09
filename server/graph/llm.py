from __future__ import annotations

import json
import logging
import os
import time
from typing import TypeVar

import groq
from groq import Groq
from pydantic import BaseModel, ValidationError

logger = logging.getLogger("graph.llm")

MODEL = "llama-3.3-70b-versatile"

# Real Groq-API-level failures (as opposed to a 200 response containing
# malformed JSON). `groq.APIError` is the base of the SDK's entire real
# exception hierarchy (see server/.venv/Lib/site-packages/groq/_exceptions.py):
# APIError -> {APIConnectionError -> APITimeoutError,
#              APIStatusError -> {RateLimitError, AuthenticationError, ...}}.
# Catching just APIError covers connection errors, timeouts, rate limits,
# auth failures, and 5xx responses via inheritance.
_GROQ_API_ERRORS = (groq.APIError,)

# Transient errors worth one short-backoff retry before giving up on the
# same call shape (rate limit, momentary connection blip, upstream 5xx).
# Hard failures (bad API key, malformed request) go straight to fallback --
# retrying with the same prompt/credentials can't fix those.
_RETRYABLE_GROQ_ERRORS = (groq.RateLimitError, groq.APIConnectionError, groq.InternalServerError)
_RETRY_BACKOFF_S = 0.5

T = TypeVar("T", bound=BaseModel)

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set")
        _client = Groq(api_key=api_key)
    return _client


def _call(system_prompt: str, user_prompt: str, temperature: float) -> str:
    client = _get_client()
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return resp.choices[0].message.content or ""


def _call_with_retry(system_prompt: str, user_prompt: str, temperature: float) -> str | None:
    """Wraps `_call` so a real Groq API-level failure (network error,
    timeout, rate limit, auth failure, 5xx -- anything under `groq.APIError`,
    see `_GROQ_API_ERRORS`) never propagates out of this module. Returns the
    raw response text, or None if the call ultimately failed and the caller
    should fall back rather than retry with a different prompt shape.

    Transient errors (`_RETRYABLE_GROQ_ERRORS`) get exactly one retry after a
    short backoff, since a rate limit or momentary connection blip may well
    clear up. Hard failures (bad API key, permission denied, malformed
    request) go straight to None -- retrying with the same credentials/prompt
    can't fix those, and repair-retrying at the JSON level (this module's
    other retry, for malformed JSON) is a different failure mode entirely.
    """
    try:
        return _call(system_prompt, user_prompt, temperature)
    except _GROQ_API_ERRORS as first_error:
        if isinstance(first_error, _RETRYABLE_GROQ_ERRORS):
            logger.warning(
                "Groq API call failed (%s: %s); retrying once after backoff",
                type(first_error).__name__,
                first_error,
            )
            try:
                time.sleep(_RETRY_BACKOFF_S)
                return _call(system_prompt, user_prompt, temperature)
            except _GROQ_API_ERRORS as second_error:
                logger.error(
                    "Groq API call failed again after retry (%s: %s); falling back",
                    type(second_error).__name__,
                    second_error,
                )
                return None
        logger.error(
            "Groq API call failed with a non-retryable error (%s: %s); falling back",
            type(first_error).__name__,
            first_error,
        )
        return None


def generate_structured(
    schema: type[T],
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    fallback: T | None = None,
) -> T:
    """Call Groq in JSON mode and validate against `schema`.

    One repair retry on validation failure, then falls back to `fallback` if
    given (or re-raises) -- the graph must never crash or hang because the
    LLM returned something malformed.

    This also covers real API-level failures (connection errors, timeouts,
    rate limits, auth failures -- see `_call_with_retry`): those are treated
    the same as an unrepairable malformed response and fall back to
    `fallback` rather than propagating, since there is no JSON to repair-retry
    against and every caller already supplies a safe fallback for exactly
    this "the LLM step did not produce something usable" case.
    """
    raw = _call_with_retry(system_prompt, user_prompt, temperature)
    if raw is None:
        if fallback is not None:
            return fallback
        raise RuntimeError("Groq API call failed and no fallback was provided")

    try:
        return schema.model_validate_json(raw)
    except (ValidationError, json.JSONDecodeError) as first_error:
        repair_prompt = (
            f"{user_prompt}\n\n"
            "Your previous response was not valid JSON matching the required schema.\n"
            f"Error: {first_error}\n"
            f"Previous response: {raw}\n"
            "Respond again with ONLY valid JSON matching the schema, nothing else."
        )
        raw2 = _call_with_retry(system_prompt, repair_prompt, temperature)
        if raw2 is None:
            if fallback is not None:
                return fallback
            raise RuntimeError("Groq API call failed on repair retry and no fallback was provided") from first_error

        try:
            return schema.model_validate_json(raw2)
        except (ValidationError, json.JSONDecodeError):
            if fallback is not None:
                return fallback
            raise
