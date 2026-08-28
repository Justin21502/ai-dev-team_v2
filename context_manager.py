"""Role-aware repository context selection for AI Dev Team agents."""

from __future__ import annotations

from pathlib import Path

from team_config import get_config


CONFIG = get_config()
DEFAULT_MAX_CHARS = CONFIG.context_max_chars

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


SENSITIVE_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}

SENSITIVE_SUFFIXES = {
    ".key",
    ".pem",
    ".p12",
    ".pfx",
}

BINARY_SUFFIXES = {
    ".7z",
    ".a",
    ".bin",
    ".bmp",
    ".class",
    ".dll",
    ".dylib",
    ".exe",
    ".gif",
    ".ico",
    ".jar",
    ".jpeg",
    ".jpg",
    ".o",
    ".obj",
    ".pdf",
    ".png",
    ".pyc",
    ".so",
    ".tar",
    ".tgz",
    ".webp",
    ".whl",
    ".zip",
}


def discover_project_files(
    workspace_dir: str,
) -> list[str]:
    """
    Discover text-like project files currently present in the workspace.

    Returned paths are workspace-relative POSIX paths for portability.
    Cache/build directories, team metadata, obvious binaries, and likely
    secret-bearing files are excluded.
    """
    workspace = Path(workspace_dir).resolve()

    if not workspace.exists():
        return []

    discovered = []

    for candidate in workspace.rglob("*"):
        try:
            if not candidate.is_file():
                continue

            absolute = candidate.resolve()
            relative = absolute.relative_to(workspace)
        except (OSError, ValueError):
            continue

        if any(
            part in IGNORED_DIRS
            for part in relative.parts[:-1]
        ):
            continue

        name = relative.name
        lower_name = name.lower()
        suffix = relative.suffix.lower()

        if name in IGNORED_FILES:
            continue

        if lower_name in SENSITIVE_FILE_NAMES:
            continue

        if (
            lower_name.startswith(".env.")
            and lower_name != ".env.example"
        ):
            continue

        if suffix in SENSITIVE_SUFFIXES:
            continue

        if suffix in BINARY_SUFFIXES:
            continue

        discovered.append(
            relative.as_posix()
        )

    return sorted(
        set(discovered),
        key=str.lower,
    )


def select_context_files(
    paths: list[str],
    workspace_dir: str,
    role: str,
    *,
    focus_paths: list[str] | None = None,
) -> list[tuple[Path, Path, str]]:
    """
    Select and order context files for an agent role.

    Files explicitly named in focus_paths are placed first. Remaining files
    retain the normal deterministic role/category ordering.

    Returns:
        (absolute_path, relative_path, category)
    """
    normalized = _normalize_paths(paths, workspace_dir)

    selected = [
        (absolute, relative, _classify(relative))
        for absolute, relative in normalized
    ]

    focus_order = {}

    if focus_paths:
        workspace = Path(workspace_dir).resolve()

        for index, value in enumerate(focus_paths):
            candidate = Path(value)

            if not candidate.is_absolute():
                candidate = workspace / candidate

            try:
                relative = (
                    candidate.resolve()
                    .relative_to(workspace)
                    .as_posix()
                )
            except (OSError, ValueError):
                continue

            focus_order.setdefault(relative, index)

    def sort_key(item):
        relative = item[1].as_posix()

        if relative in focus_order:
            return (
                0,
                focus_order[relative],
                0,
                relative.lower(),
            )

        return (
            1,
            0,
            _role_priority(role, item[2]),
            relative.lower(),
        )

    selected.sort(key=sort_key)

    return selected


def build_context(
    paths: list[str],
    workspace_dir: str,
    role: str,
    *,
    max_chars: int | None = None,
    focus_paths: list[str] | None = None,
) -> str:
    """
    Build bounded, workspace-relative repository context for an agent.

    When several files are explicitly focused, each receives a bounded share
    of the budget so one large file cannot hide the other implicated files.
    """
    if max_chars is None:
        max_chars = DEFAULT_MAX_CHARS

    if max_chars <= 0:
        return "(Repository context disabled by context budget.)"[:max_chars]

    files = select_context_files(
        paths,
        workspace_dir,
        role,
        focus_paths=focus_paths,
    )

    if not files:
        return "(No generated files are currently available.)"[:max_chars]

    workspace = Path(workspace_dir).resolve()

    focus_names = set()

    for value in focus_paths or []:
        candidate = Path(value)

        if not candidate.is_absolute():
            candidate = workspace / candidate

        try:
            relative = (
                candidate.resolve()
                .relative_to(workspace)
                .as_posix()
            )
        except (OSError, ValueError):
            continue

        focus_names.add(relative)

    selected_focus_names = {
        relative.as_posix()
        for _, relative, _ in files
        if relative.as_posix() in focus_names
    }

    # Reserve roughly two-thirds of the total budget for explicitly focused
    # files. The remaining third is available for surrounding repository
    # context. With multiple focus files, divide that reserved space evenly.
    focus_cap = None

    if len(selected_focus_names) > 1:
        focus_pool = max_chars * 2 // 3
        focus_cap = max(
            220,
            focus_pool // len(selected_focus_names),
        )

    chunks = []
    omitted = 0

    def current_length() -> int:
        return len("\n\n".join(chunks))

    for absolute, relative, category in files:
        try:
            content = absolute.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError:
            omitted += 1
            continue

        header = (
            f"### FILE: {relative.as_posix()}\n"
            f"Category: {category}\n"
            "```\n"
        )
        footer = "\n```"
        truncation = "\n... [FILE TRUNCATED BY CONTEXT BUDGET]"

        used = current_length()
        separator_cost = 2 if chunks else 0
        remaining = max_chars - used - separator_cost

        if remaining <= 0:
            omitted += 1
            continue

        allowed = remaining

        if (
            focus_cap is not None
            and relative.as_posix() in selected_focus_names
        ):
            allowed = min(allowed, focus_cap)

        full_chunk = header + content + footer

        if len(full_chunk) <= allowed:
            chunks.append(full_chunk)
            continue

        minimum_room = (
            len(header)
            + len(truncation)
            + len(footer)
            + 20
        )

        if allowed >= minimum_room:
            content_room = (
                allowed
                - len(header)
                - len(truncation)
                - len(footer)
            )

            chunks.append(
                header
                + content[:content_room]
                + truncation
                + footer
            )

        omitted += 1

    result = "\n\n".join(chunks)

    if omitted:
        notice = (
            f"\n\n[CONTEXT NOTICE: {omitted} file(s) omitted or truncated "
            f"because the {max_chars:,}-character context budget was reached.]"
        )

        if len(result) + len(notice) <= max_chars:
            result += notice
        elif len(notice) < max_chars:
            keep = max_chars - len(notice)
            result = result[:keep].rstrip() + notice

    return result[:max_chars]


def build_context_report(
    paths: list[str],
    workspace_dir: str,
    role: str,
    *,
    max_chars: int | None = None,
    focus_paths: list[str] | None = None,
) -> tuple[str, dict]:
    """
    Build normal agent context plus observability metadata.

    This intentionally delegates context generation to build_context() so
    observability cannot change file selection or budgeting behavior.
    """
    if max_chars is None:
        max_chars = DEFAULT_MAX_CHARS

    selected = select_context_files(
        paths,
        workspace_dir,
        role,
        focus_paths=focus_paths,
    )

    context = build_context(
        paths,
        workspace_dir,
        role,
        max_chars=max_chars,
        focus_paths=focus_paths,
    )

    selected_files = [
        relative.as_posix()
        for _, relative, _ in selected
    ]

    visible_files = []

    for line in context.splitlines():
        prefix = "### FILE: "

        if not line.startswith(prefix):
            continue

        value = line[len(prefix):].strip()

        if value and value not in visible_files:
            visible_files.append(value)

    normalized_focus = []

    workspace = Path(workspace_dir).resolve()

    for value in focus_paths or []:
        candidate = Path(value)

        if not candidate.is_absolute():
            candidate = workspace / candidate

        try:
            relative = (
                candidate.resolve()
                .relative_to(workspace)
                .as_posix()
            )
        except (OSError, ValueError):
            continue

        if relative not in normalized_focus:
            normalized_focus.append(relative)

    focused_visible = [
        value
        for value in normalized_focus
        if value in visible_files
    ]

    omitted_files = [
        value
        for value in selected_files
        if value not in visible_files
    ]

    report = {
        "role": role.lower(),
        "budget_max": max_chars,
        "budget_used": len(context),
        "budget_percent": (
            round(
                (len(context) / max_chars) * 100,
                1,
            )
            if max_chars > 0
            else 0.0
        ),
        "selected_count": len(selected_files),
        "visible_count": len(visible_files),
        "omitted_count": len(omitted_files),
        "focus_count": len(normalized_focus),
        "focused_visible_count": len(focused_visible),
        "selected_files": selected_files,
        "visible_files": visible_files,
        "focused_files": normalized_focus,
        "focused_visible_files": focused_visible,
        "omitted_files": omitted_files,
    }

    return context, report

