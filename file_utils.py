import os
import re
from pathlib import Path

# Matches:
# ### FILE: path/to/file.py
# ```<optional lang>
# <content>
# ```
FILE_BLOCK_RE = re.compile(
    r"###\s*FILE:\s*(?P<path>\S+)\s*\n```[a-zA-Z0-9_+-]*\n(?P<content>.*?)```",
    re.DOTALL,
)


def extract_files(text: str) -> dict[str, str]:
    """Parse an agent's response into {relative_path: file_contents}."""
    files = {}

    for match in FILE_BLOCK_RE.finditer(text):
        path = match.group("path").strip()
        content = match.group("content")
        files[path] = content

    return files


def _normalize_relative_path(rel_path: str, base_dir: str) -> str | None:
    """
    Normalize an agent-provided path relative to the workspace.

    Agents sometimes incorrectly return paths such as:

        workspace/src/main.py

    even though `workspace` is already the configured base directory.

    This function strips that redundant workspace prefix while rejecting
    absolute paths and path traversal attempts.
    """
    if not rel_path:
        return None

    # Normalize Windows separators so the same rules work everywhere.
    rel_path = rel_path.replace("\\", "/").strip()

    # Reject absolute Unix paths.
    if rel_path.startswith("/"):
        return None

    # Reject Windows drive paths such as C:/foo.py.
    if re.match(r"^[A-Za-z]:/", rel_path):
        return None

    # Normalize the path without allowing it to escape the workspace.
    normalized = os.path.normpath(rel_path)

    if normalized in ("", "."):
        return None

    if normalized == ".." or normalized.startswith(".." + os.sep):
        return None

    # Convert the configured workspace directory to a normalized name.
    base_name = Path(base_dir).resolve().name

    # Handle agents returning "workspace/foo.py" when the base directory
    # itself is named "workspace".
    normalized_forward = normalized.replace(os.sep, "/")
    redundant_prefix = base_name + "/"

    if normalized_forward.startswith(redundant_prefix):
        normalized_forward = normalized_forward[len(redundant_prefix):]

    # Re-check after removing the redundant prefix.
    if not normalized_forward or normalized_forward == ".":
        return None

    if normalized_forward == ".." or normalized_forward.startswith("../"):
        return None

    # Reject an embedded Codespace/team workspace path.
    #
    # Example of a bad agent path:
    #   workspace/workspaces/ai-dev-team_v2/workspace/tests/test.py
    #
    # After removing the redundant first "workspace/" prefix, this becomes:
    #   workspaces/ai-dev-team_v2/workspace/tests/test.py
    #
    # A real project may have normal subdirectories such as "src/" or
    # "tests/", but recreating "workspaces/<team>/workspace/" inside the
    # project is always an accidental path echo.
    parts = normalized_forward.split("/")
    workspace_indexes = [
        i for i, part in enumerate(parts) if part == "workspaces"
    ]

    for i in workspace_indexes:
        if (
            i + 2 < len(parts)
            and parts[i + 2] == Path(base_dir).resolve().name
        ):
            return None

    return normalized_forward


def write_files(files: dict[str, str], base_dir: str) -> list[str]:
    """
    Write parsed files safely inside base_dir.

    Agent paths are treated as workspace-relative paths. A redundant
    workspace prefix is automatically removed.
    """
    written = []

    base_path = Path(base_dir).resolve()
    base_path.mkdir(parents=True, exist_ok=True)

    for rel_path, content in files.items():
        safe_path = _normalize_relative_path(rel_path, str(base_path))

        if safe_path is None:
            continue

        full_path = (base_path / safe_path).resolve()

        # Final containment check. This protects against anything that
        # slipped through normalization.
        try:
            full_path.relative_to(base_path)
        except ValueError:
            continue

        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

        written.append(str(full_path))

    return written


def read_files_as_text(paths: list[str]) -> str:
    """Concatenate files with headers, for feeding back to an agent as context."""
    chunks = []

    for path in paths:
        with open(path, encoding="utf-8") as f:
            chunks.append(
                f"### FILE: {path}\n```\n{f.read()}\n```"
            )

    return "\n\n".join(chunks)
