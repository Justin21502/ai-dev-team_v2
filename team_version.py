"""Version helpers for AI Dev Team."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VERSION_FILE = ROOT / "VERSION"
DISTRIBUTION_NAME = "ai-dev-team"


def get_version() -> str:
    """Resolve the AI Dev Team version.

    Source checkouts prefer the VERSION file.
    Installed distributions fall back to package metadata.
    """
    if VERSION_FILE.exists():
        value = VERSION_FILE.read_text(
            encoding="utf-8"
        ).strip()

        if value:
            return value

    try:
        return version(DISTRIBUTION_NAME)
    except PackageNotFoundError:
        return "unknown"


def show_version() -> None:
    print(
        f"AI Dev Team v{get_version()}"
    )
