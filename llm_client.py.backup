"""Robust Groq/OpenAI-compatible client for the AI Dev Team.

The project uses Groq because it offers a generous free tier and an
OpenAI-compatible API.  The client intentionally keeps model selection in one
place and can fall back when a configured model is unavailable.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Iterable

from openai import OpenAI

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
PRIMARY_MODEL = os.environ.get("AI_TEAM_PRIMARY_MODEL", "openai/gpt-oss-120b")
FAST_MODEL = os.environ.get("AI_TEAM_FAST_MODEL", "openai/gpt-oss-20b")
DEFAULT_MODEL = os.environ.get("AI_TEAM_MODEL", PRIMARY_MODEL)
FALLBACK_MODEL = os.environ.get("AI_TEAM_FALLBACK_MODEL", FAST_MODEL)
MAX_RETRIES = int(os.environ.get("AI_TEAM_MAX_RETRIES", "2"))
RETRY_BASE_SECONDS = float(os.environ.get("AI_TEAM_RETRY_BASE_SECONDS", "2"))

_client: OpenAI | None = None
_env_loaded = False


def _load_dotenv_file() -> None:
    """Load a local .env without requiring python-dotenv.

    Existing environment variables always win. This makes the Codespace
    experience work immediately after `cp .env.example .env`, while GitHub
    Codespaces secrets continue to work normally.
    """
    global _env_loaded
    if _env_loaded:
        return
    _env_loaded = True

    root = Path(__file__).resolve().parent
    env_file = root / ".env"
    if not env_file.exists():
        return

    for raw in env_file.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def get_client() -> OpenAI:
    global _client
    _load_dotenv_file()

    if _client is not None:
        return _client

    token = os.environ.get("GROQ_API_KEY")
    if not token:
        raise RuntimeError(
            "No GROQ_API_KEY found. Put it in .env or configure it as a "
            "GitHub Codespaces secret. Get a free key at "
            "https://console.groq.com/keys"
        )

    _client = OpenAI(base_url=GROQ_BASE_URL, api_key=token)
    return _client


def _is_retryable(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    return status in {408, 409, 429, 500, 502, 503, 504}


def _is_model_not_found(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    message = str(exc).lower()
    return status == 404 or "model_not_found" in message or "does not exist" in message


def _request(client: OpenAI, messages, model: str, temperature: float):
    """Make one request, using conservative output limits for free-tier use."""
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    # GPT-OSS supports reasoning_effort; don't force it on arbitrary custom
    # models. The env flag is opt-in so custom model compatibility is preserved.
    if os.environ.get("AI_TEAM_REASONING_EFFORT"):
        kwargs["reasoning_effort"] = os.environ["AI_TEAM_REASONING_EFFORT"]
    if os.environ.get("AI_TEAM_MAX_OUTPUT_TOKENS"):
        kwargs["max_completion_tokens"] = int(os.environ["AI_TEAM_MAX_OUTPUT_TOKENS"])
    return client.chat.completions.create(**kwargs)


def chat(messages, model: str | None = None, temperature: float = 0.3) -> str:
    """Send a chat completion with retries and an automatic model fallback."""
    client = get_client()
    requested = model or DEFAULT_MODEL
    candidates: list[str] = [requested]
    if FALLBACK_MODEL and FALLBACK_MODEL not in candidates:
        candidates.append(FALLBACK_MODEL)

    last_error: Exception | None = None

    for candidate_index, candidate in enumerate(candidates):
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = _request(client, messages, candidate, temperature)
                text = response.choices[0].message.content or ""
                if candidate != requested:
                    print(
                        f"[LLM] Model '{requested}' unavailable; using fallback '{candidate}'.",
                        flush=True,
                    )
                return text
            except Exception as exc:
                last_error = exc
                if _is_model_not_found(exc) and candidate_index < len(candidates) - 1:
                    break
                if not _is_retryable(exc) or attempt >= MAX_RETRIES:
                    raise
                delay = RETRY_BASE_SECONDS * (2**attempt)
                print(
                    f"[LLM] Request failed ({type(exc).__name__}); retrying in {delay:g}s...",
                    flush=True,
                )
                time.sleep(delay)

    assert last_error is not None
    raise last_error
