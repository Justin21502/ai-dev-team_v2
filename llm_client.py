"""Robust Groq/OpenAI-compatible client for the AI Dev Team.

Includes:
- automatic model fallback
- retries
- live streaming
- exact API-reported token usage
- per-agent usage tracking
"""

from __future__ import annotations

import os
import sys
import time

from openai import OpenAI

from team_config import get_config
from usage_tracker import tracker
from team_events import events

config = get_config()

GROQ_BASE_URL = config.groq_base_url
PRIMARY_MODEL = config.primary_model
FAST_MODEL = config.fast_model
DEFAULT_MODEL = config.default_model
FALLBACK_MODEL = config.fallback_model
MAX_RETRIES = config.max_retries
RETRY_BASE_SECONDS = config.retry_base_seconds

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client

    if _client is not None:
        return _client

    config = get_config()
    token = config.groq_api_key

    if not token:
        raise RuntimeError(
            "No GROQ_API_KEY found. Put it in the "
            "project .env or configure it in the "
            "process environment."
        )

    _client = OpenAI(
        base_url=config.groq_base_url,
        api_key=token,
    )

    return _client



def _classify_api_failure(
    exc: Exception,
) -> str:
    """Classify an API failure for retry/fallback decisions."""
    status = getattr(
        exc,
        "status_code",
        None,
    )

    message = str(exc).lower()

    if status in {401, 403}:
        return "auth"

    if status == 404 or any(
        term in message
        for term in (
            "model_not_found",
            "model not found",
            "does not exist",
            "unsupported model",
        )
    ):
        return "model"

    if status in {
        408,
        409,
        429,
        500,
        502,
        503,
        504,
    }:
        return "transient"

    if any(
        term in message
        for term in (
            "api key",
            "authentication",
            "unauthorized",
            "forbidden",
            "invalid key",
        )
    ):
        return "auth"

    return "fatal"


def _is_retryable(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)

    return status in {
        408,
        409,
        429,
        500,
        502,
        503,
        504,
    }


def _is_model_not_found(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    message = str(exc).lower()

    return (
        status == 404
        or "model_not_found" in message
        or "does not exist" in message
    )


def _request(client, messages, model, temperature):
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
        "stream_options": {
            "include_usage": True,
        },
    }

    config = get_config()

    if config.reasoning_effort:
        kwargs[
            "reasoning_effort"
        ] = config.reasoning_effort

    if config.max_output_tokens is not None:
        kwargs[
            "max_completion_tokens"
        ] = config.max_output_tokens

    return client.chat.completions.create(**kwargs)


def _emit_model_fallback(
    *,
    agent_name: str,
    from_model: str,
    to_model: str,
    reason: str,
) -> None:
    """Publish one operational model-fallback event."""
    events.emit(
        "TEAM_TELEMETRY",
        fallback_agent=agent_name,
        fallback_from_model=from_model,
        fallback_to_model=to_model,
        fallback_reason=reason,
        fallback_active=True,
    )

    events.emit(
        "TEAM_LOG",
        agent=agent_name,
        message=(
            f"Model fallback: {from_model} -> "
            f"{to_model} ({reason})."
        ),
    )


def chat(
    messages,
    model: str | None = None,
    temperature: float = 0.3,
    agent_name: str = "Unknown",
) -> str:
    """Send a streaming chat completion and record exact usage."""

    client = get_client()

    requested = model or DEFAULT_MODEL

    candidates = [requested]

    if FALLBACK_MODEL and FALLBACK_MODEL not in candidates:
        candidates.append(FALLBACK_MODEL)

    last_error = None

    for candidate_index, candidate in enumerate(candidates):

        for attempt in range(MAX_RETRIES + 1):

            try:
                stream = _request(
                    client,
                    messages,
                    candidate,
                    temperature,
                )

                pieces = []
                final_usage = None

                # Send generation status to the dashboard.
                events.emit(
                    "TEAM_TELEMETRY",
                    current_model=candidate,
                )
                events.emit(
                    "TEAM_LOG",
                    agent=agent_name,
                    message=f"{candidate} is generating",
                )

                for chunk in stream:

                    # The final streaming chunk can contain usage.
                    usage = getattr(chunk, "usage", None)

                    if usage is not None:
                        final_usage = usage

                    choices = getattr(chunk, "choices", None)

                    if not choices:
                        continue

                    delta = getattr(
                        choices[0],
                        "delta",
                        None,
                    )

                    if delta is None:
                        continue

                    content = getattr(
                        delta,
                        "content",
                        None,
                    )

                    if content:
                        pieces.append(content)

                input_tokens = 0
                output_tokens = 0
                total_tokens = 0

                if final_usage is not None:
                    input_tokens = (
                        getattr(
                            final_usage,
                            "prompt_tokens",
                            0,
                        )
                        or 0
                    )

                    output_tokens = (
                        getattr(
                            final_usage,
                            "completion_tokens",
                            0,
                        )
                        or 0
                    )

                    total_tokens = (
                        getattr(
                            final_usage,
                            "total_tokens",
                            0,
                        )
                        or 0
                    )

                tracker.record(
                    agent=agent_name,
                    model=candidate,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                )

                return "".join(pieces)

            except Exception as exc:

                last_error = exc
                failure_type = _classify_api_failure(
                    exc
                )

                if failure_type == "model":
                    if candidate_index < len(candidates) - 1:
                        next_model = candidates[
                            candidate_index + 1
                        ]

                        _emit_model_fallback(
                            agent_name=agent_name,
                            from_model=candidate,
                            to_model=next_model,
                            reason="model_unavailable",
                        )

                        break

                    raise

                if failure_type in {
                    "auth",
                    "fatal",
                }:
                    raise

                if failure_type != "transient":
                    raise

                if attempt >= MAX_RETRIES:
                    if candidate_index < len(candidates) - 1:
                        next_model = candidates[
                            candidate_index + 1
                        ]

                        _emit_model_fallback(
                            agent_name=agent_name,
                            from_model=candidate,
                            to_model=next_model,
                            reason="retries_exhausted",
                        )

                        break

                    raise

                delay = RETRY_BASE_SECONDS * (2**attempt)

                events.emit(
                    "TEAM_LOG",
                    agent=agent_name,
                    message=(
                        f"Request failed ({type(exc).__name__}); "
                        f"retrying in {delay:g}s..."
                    ),
                )

                time.sleep(delay)

    assert last_error is not None

    raise last_error
