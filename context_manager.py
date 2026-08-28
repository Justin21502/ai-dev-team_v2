"""Role-aware repository context selection for AI Dev Team agents."""

from __future__ import annotations

import os
from pathlib import Path


DEFAULT_MAX_CHARS = int(
    os.environ.get("AI_TEAM_CONTEXT_MAX_CHARS", "30000")
)

IGNORED_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".team",
    ".venv",
    "venv",
    "node_modules",
}

IGNORED_FILES = {
    "run_history.json",
    "run_log.json",
}

CONFIG_NAMES = {
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "setup.py",
    "setup.cfg",
    "tox.ini",
    "pytest.ini",
    ".env.example",
}

DOC_NAMES = {
    "README.md",
    "README.rst",
    "README.txt",
    "LICENSE",
    "LICENSE.txt",
    "LICENSE.md",
}


def _is_test_path(path: Path) -> bool:
    name = path.name

    return (
        "tests" in path.parts[:-1]
        or name.startswith("test_")
        or name.endswith("_test.py")
    )


def _classify(path: Path) -> str:
    """Classify a project-relative file for context selection."""
    if _is_test_path(path):
        return "test"

    if path.name in CONFIG_NAMES:
        return "config"

    if path.name in DOC_NAMES:
        return "docs"

    return "application"


def _normalize_paths(
    paths: list[str],
    workspace_dir: str,
) -> list[tuple[Path, Path]]:
    """
    Return unique existing files as:
        (absolute_path, workspace_relative_path)
    """
    workspace = Path(workspace_dir).resolve()
    found = []
    seen = set()

    for value in paths:
        path = Path(value)

        if not path.is_absolute():
            path = workspace / path

        try:
            absolute = path.resolve()
            relative = absolute.relative_to(workspace)
        except (OSError, ValueError):
            continue

        if absolute in seen:
            continue

        if not absolute.is_file():
            continue

        if relative.name in IGNORED_FILES:
            continue

        if any(part in IGNORED_DIRS for part in relative.parts):
            continue

        seen.add(absolute)
        found.append((absolute, relative))

    return found


def _role_priority(role: str, category: str) -> int:
    """
    Lower numbers are selected first.

    This intentionally uses simple deterministic policy before introducing
    semantic relevance or traceback analysis in later versions.
    """
    role = role.lower()

    policies = {
        "reviewer": {
            "application": 0,
            "config": 1,
            "test": 2,
            "docs": 3,
        },
        "security": {
            "application": 0,
            "config": 1,
            "docs": 2,
            "test": 3,
        },
        "tester": {
            "application": 0,
            "config": 1,
            "docs": 2,
            "test": 3,
        },
        "developer": {
            "application": 0,
            "config": 1,
            "test": 2,
            "docs": 3,
        },
        "debugger": {
            "application": 0,
            "test": 1,
            "config": 2,
            "docs": 3,
        },
    }

    policy = policies.get(role, policies["developer"])
    return policy.get(category, 9)


def select_context_files(
    paths: list[str],
    workspace_dir: str,
    role: str,
) -> list[tuple[Path, Path, str]]:
    """
    Select and order context files for an agent role.

    Returns:
        (absolute_path, relative_path, category)
    """
    normalized = _normalize_paths(paths, workspace_dir)

    selected = [
        (absolute, relative, _classify(relative))
        for absolute, relative in normalized
    ]

    selected.sort(
        key=lambda item: (
            _role_priority(role, item[2]),
            item[1].as_posix().lower(),
        )
    )

    return selected


def build_context(
    paths: list[str],
    workspace_dir: str,
    role: str,
    *,
    max_chars: int | None = None,
) -> str:
    """
    Build bounded, workspace-relative repository context for an agent.
    """
    if max_chars is None:
        max_chars = DEFAULT_MAX_CHARS

    if max_chars <= 0:
        return "(Repository context disabled by context budget.)"

    files = select_context_files(
        paths,
        workspace_dir,
        role,
    )

    if not files:
        return "(No generated files are currently available.)"

    chunks = []
    used = 0
    omitted = 0

    for absolute, relative, category in files:
        try:
            content = absolute.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError:
            continue

        header = (
            f"### FILE: {relative.as_posix()}\n"
            f"Category: {category}\n"
            "```\n"
        )
        footer = "\n```"

        full_chunk = header + content + footer

        remaining = max_chars - used

        if remaining <= 0:
            omitted += 1
            continue

        if len(full_chunk) <= remaining:
            chunks.append(full_chunk)
            used += len(full_chunk)
            continue

        # Include a useful partial view rather than exceeding the budget.
        minimum_room = len(header) + len(footer) + 80

        if remaining >= minimum_room:
            available = remaining - len(header) - len(footer)
            truncated = content[:available]

            chunks.append(
                header
                + truncated
                + "\n... [FILE TRUNCATED BY CONTEXT BUDGET]"
                + footer
            )
            used = max_chars

        omitted += 1

    result = "\n\n".join(chunks)

    if omitted:
        notice = (
            f"\n\n[CONTEXT NOTICE: {omitted} file(s) omitted or truncated "
            f"because the {max_chars:,}-character context budget was reached.]"
        )

        # The configured budget is a hard ceiling, including metadata.
        if len(result) + len(notice) <= max_chars:
            result += notice
        elif len(notice) < max_chars:
            keep = max_chars - len(notice)
            result = result[:keep].rstrip() + notice
        else:
            result = result[:max_chars]

    return result[:max_chars]
