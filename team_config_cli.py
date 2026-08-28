"""CLI views for AI Dev Team configuration."""

from __future__ import annotations

from model_router import (
    ROLE_DEFAULT_TIERS,
    resolve_role_model,
)
from team_config import get_config


def show_config() -> None:
    """Display resolved non-secret team configuration."""
    config = get_config()

    print()
    print("AI DEV TEAM — CONFIGURATION")
    print()

    print(f"Project root:       {config.project_root}")

    print(
        "Environment file:   "
        + (
            str(config.env_file)
            if config.env_file.exists()
            else "not present"
        )
    )

    print(
        "Groq API key:       "
        + (
            "configured"
            if config.groq_api_key
            else "not configured"
        )
    )

    print()
    print("Models")
    print(f"  Primary:          {config.primary_model}")
    print(f"  Fast:             {config.fast_model}")
    print(f"  Default:          {config.default_model}")
    print(f"  Fallback:         {config.fallback_model}")

    print()
    print("Generation")
    print(f"  Max retries:      {config.max_retries}")
    print(
        f"  Retry delay:      "
        f"{config.retry_base_seconds:g}s"
    )

    print(
        "  Reasoning effort: "
        + (
            config.reasoning_effort
            or "provider default"
        )
    )

    print(
        "  Output tokens:    "
        + (
            str(config.max_output_tokens)
            if config.max_output_tokens
            is not None
            else "provider default"
        )
    )

    print()
    print("Team workflow")
    print(
        f"  Review rounds:    "
        f"{config.max_review_iterations}"
    )
    print(
        f"  Security rounds:  "
        f"{config.max_security_iterations}"
    )
    print(
        f"  Test rounds:      "
        f"{config.max_test_iterations}"
    )
    print(
        f"  Research:         "
        f"{'enabled' if config.enable_research else 'disabled'}"
    )

    print()
    print(
        f"Context budget:     "
        f"{config.context_max_chars:,} chars"
    )
    print()


def show_models() -> None:
    """Display the resolved model route for every role."""
    config = get_config()

    print()
    print("AI DEV TEAM — MODELS")
    print()

    print(f"Primary:   {config.primary_model}")
    print(f"Fast:      {config.fast_model}")
    print(f"Fallback:  {config.fallback_model}")
    print()

    width = max(
        len(role)
        for role in ROLE_DEFAULT_TIERS
    )

    for role, default_tier in (
        ROLE_DEFAULT_TIERS.items()
    ):
        model = resolve_role_model(role)

        print(
            f"{role:<{width}}  "
            f"{default_tier:<7}  "
            f"{model}"
        )

    print()
