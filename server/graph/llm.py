from __future__ import annotations

import json
import os
from typing import TypeVar

from groq import Groq
from pydantic import BaseModel, ValidationError

MODEL = "llama-3.3-70b-versatile"

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
    """
    raw = _call(system_prompt, user_prompt, temperature)
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
        raw2 = _call(system_prompt, repair_prompt, temperature)
        try:
            return schema.model_validate_json(raw2)
        except (ValidationError, json.JSONDecodeError):
            if fallback is not None:
                return fallback
            raise
