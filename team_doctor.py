"""Environment diagnostics for the AI Dev Team."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from model_router import (
    ROLE_DEFAULT_TIERS,
    route_model,
)
from team_config import get_config
from team_version import get_version


PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"


def _check(
    results: list[tuple[str, str, str]],
    name: str,
    status: str,
    detail: str,
) -> None:
    results.append(
        (
            name,
            status,
            detail,
        )
    )


def _check_python(
    results: list[tuple[str, str, str]],
) -> None:
    version = sys.version_info

    text = (
        f"{version.major}."
        f"{version.minor}."
        f"{version.micro}"
    )

    if version >= (3, 10):
        status = PASS
    else:
        status = FAIL

    _check(
        results,
        "Python",
        status,
        text,
    )


def _check_command(
    results: list[tuple[str, str, str]],
    name: str,
    command: str,
    *,
    required: bool,
) -> None:
    path = shutil.which(command)

    if path:
        _check(
            results,
            name,
            PASS,
            path,
        )
        return

    _check(
        results,
        name,
        FAIL if required else WARN,
        "not found",
    )


def _check_directory(
    results: list[tuple[str, str, str]],
    name: str,
    path: Path,
) -> None:
    try:
        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        probe = path / ".team_doctor_probe"

        probe.write_text(
            "ok",
            encoding="utf-8",
        )

        probe.unlink()

    except OSError as exc:
        _check(
            results,
            name,
            FAIL,
            str(exc),
        )
        return

    _check(
        results,
        name,
        PASS,
        str(path),
    )


def _check_routing(
    results: list[tuple[str, str, str]],
) -> None:
    failures = []

    for role in ROLE_DEFAULT_TIERS:
        try:
            route = route_model(role)

            if not route.model:
                failures.append(
                    f"{role}: empty model"
                )

        except Exception as exc:
            failures.append(
                f"{role}: {exc}"
            )

    if failures:
        _check(
            results,
            "Model routing",
            FAIL,
            "; ".join(failures),
        )
        return

    _check(
        results,
        "Model routing",
        PASS,
        (
            f"{len(ROLE_DEFAULT_TIERS)} "
            "agent roles resolved"
        ),
    )


def run_doctor() -> int:
    """Run local diagnostics without making API requests."""
    results: list[
        tuple[str, str, str]
    ] = []

    try:
        config = get_config()
    except Exception as exc:
        print()
        print("AI DEV TEAM — DOCTOR")
        print()
        print(
            f"[{FAIL}] Configuration: {exc}"
        )
        print()
        print("Doctor result: FAIL")
        print()

        return 1

    _check(
        results,
        "Version",
        PASS,
        get_version(),
    )

    _check(
        results,
        "Configuration",
        PASS,
        "central config loaded",
    )

    if config.env_file.exists():
        _check(
            results,
            ".env",
            PASS,
            str(config.env_file),
        )
    else:
        _check(
            results,
            ".env",
            WARN,
            (
                "not found; process environment "
                "may still provide configuration"
            ),
        )

    if config.groq_api_key:
        _check(
            results,
            "Groq API key",
            PASS,
            "configured",
        )
    else:
        _check(
            results,
            "Groq API key",
            FAIL,
            "GROQ_API_KEY is not configured",
        )

    _check(
        results,
        "Primary model",
        PASS,
        config.primary_model,
    )

    _check(
        results,
        "Fast model",
        PASS,
        config.fast_model,
    )

    _check(
        results,
        "Fallback model",
        PASS,
        config.fallback_model,
    )

    _check_python(results)

    _check_command(
        results,
        "pytest",
        "pytest",
        required=True,
    )

    _check_command(
        results,
        "Ruff",
        "ruff",
        required=False,
    )

    workspace = (
        config.project_root
        / "workspace"
    )

    history = (
        workspace
        / ".team"
        / "runs"
    )

    _check_directory(
        results,
        "Workspace",
        workspace,
    )

    _check_directory(
        results,
        "Run history",
        history,
    )

    _check_routing(results)

    print()
    print("AI DEV TEAM — DOCTOR")
    print()

    width = max(
        len(name)
        for name, _, _ in results
    )

    for name, status, detail in results:
        print(
            f"[{status:<4}] "
            f"{name:<{width}}  "
            f"{detail}"
        )

    failures = sum(
        status == FAIL
        for _, status, _ in results
    )

    warnings = sum(
        status == WARN
        for _, status, _ in results
    )

    passes = sum(
        status == PASS
        for _, status, _ in results
    )

    print()
    print(
        f"Checks: {passes} passed, "
        f"{warnings} warnings, "
        f"{failures} failed"
    )

    if failures:
        overall = FAIL
        exit_code = 1
    elif warnings:
        overall = WARN
        exit_code = 0
    else:
        overall = PASS
        exit_code = 0

    print(
        f"Doctor result: {overall}"
    )
    print()

    return exit_code


def main() -> None:
    raise SystemExit(
        run_doctor()
    )


if __name__ == "__main__":
    main()
