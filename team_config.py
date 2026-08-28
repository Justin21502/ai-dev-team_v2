"""Centralized configuration for the AI Dev Team.

Configuration precedence:

    process environment
        ↓
    project-root .env
        ↓
    built-in defaults

The module intentionally has no dependency on llm_client so configuration
can be loaded before model routing or API clients are initialized.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"


DEFAULT_PRIMARY_MODEL = "openai/gpt-oss-120b"
DEFAULT_FAST_MODEL = "openai/gpt-oss-20b"

DEFAULT_GROQ_BASE_URL = (
    "https://api.groq.com/openai/v1"
)


_ENV_LOADED = False


def load_environment() -> None:
    """Load project .env values without overriding process variables."""
    global _ENV_LOADED

    if _ENV_LOADED:
        return

    _ENV_LOADED = True

    if not ENV_FILE.exists():
        return

    for raw in ENV_FILE.read_text().splitlines():
        line = raw.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        key, value = line.split("=", 1)

        key = key.strip()
        value = value.strip()

        if not key:
            continue

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {'"', "'"}
        ):
            value = value[1:-1]

        os.environ.setdefault(
            key,
            value,
        )


def _env(
    name: str,
    default: str | None = None,
) -> str | None:
    load_environment()
    return os.environ.get(name, default)


def _env_int(
    name: str,
    default: int,
) -> int:
    value = _env(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(
            f"{name} must be an integer; "
            f"received {value!r}."
        ) from exc


def _env_float(
    name: str,
    default: float,
) -> float:
    value = _env(name)

    if value is None:
        return default

    try:
        return float(value)
    except ValueError as exc:
        raise RuntimeError(
            f"{name} must be numeric; "
            f"received {value!r}."
        ) from exc


def _env_bool(
    name: str,
    default: bool,
) -> bool:
    value = _env(name)

    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return True

    if normalized in {
        "0",
        "false",
        "no",
        "off",
    }:
        return False

    raise RuntimeError(
        f"{name} must be true or false; "
        f"received {value!r}."
    )


@dataclass(frozen=True)
class TeamConfig:
    """Resolved runtime configuration."""

    project_root: Path
    env_file: Path

    groq_base_url: str
    groq_api_key: str | None

    primary_model: str
    fast_model: str
    default_model: str
    fallback_model: str

    max_retries: int
    retry_base_seconds: float

    reasoning_effort: str | None
    max_output_tokens: int | None

    context_max_chars: int

    max_review_iterations: int
    max_security_iterations: int
    max_test_iterations: int

    enable_research: bool


def get_config() -> TeamConfig:
    """Resolve the current configuration."""
    load_environment()

    primary = (
        _env(
            "AI_TEAM_PRIMARY_MODEL",
            DEFAULT_PRIMARY_MODEL,
        )
        or DEFAULT_PRIMARY_MODEL
    )

    fast = (
        _env(
            "AI_TEAM_FAST_MODEL",
            DEFAULT_FAST_MODEL,
        )
        or DEFAULT_FAST_MODEL
    )

    default_model = (
        _env(
            "AI_TEAM_MODEL",
            primary,
        )
        or primary
    )

    fallback = (
        _env(
            "AI_TEAM_FALLBACK_MODEL",
            fast,
        )
        or fast
    )

    max_output_raw = _env(
        "AI_TEAM_MAX_OUTPUT_TOKENS"
    )

    max_output_tokens = None

    if max_output_raw:
        try:
            max_output_tokens = int(
                max_output_raw
            )
        except ValueError as exc:
            raise RuntimeError(
                "AI_TEAM_MAX_OUTPUT_TOKENS "
                "must be an integer."
            ) from exc

    return TeamConfig(
        project_root=PROJECT_ROOT,
        env_file=ENV_FILE,
        groq_base_url=(
            _env(
                "GROQ_BASE_URL",
                DEFAULT_GROQ_BASE_URL,
            )
            or DEFAULT_GROQ_BASE_URL
        ),
        groq_api_key=_env("GROQ_API_KEY"),
        primary_model=primary,
        fast_model=fast,
        default_model=default_model,
        fallback_model=fallback,
        max_retries=_env_int(
            "AI_TEAM_MAX_RETRIES",
            2,
        ),
        retry_base_seconds=_env_float(
            "AI_TEAM_RETRY_BASE_SECONDS",
            2.0,
        ),
        reasoning_effort=_env(
            "AI_TEAM_REASONING_EFFORT"
        ),
        max_output_tokens=max_output_tokens,
        context_max_chars=_env_int(
            "AI_TEAM_CONTEXT_MAX_CHARS",
            30000,
        ),
        max_review_iterations=_env_int(
            "MAX_REVIEW_ITERATIONS",
            2,
        ),
        max_security_iterations=_env_int(
            "MAX_SECURITY_ITERATIONS",
            1,
        ),
        max_test_iterations=_env_int(
            "MAX_TEST_ITERATIONS",
            3,
        ),
        enable_research=_env_bool(
            "ENABLE_RESEARCH",
            True,
        ),
    )


# Load .env before dependent modules initialize constants.
load_environment()
