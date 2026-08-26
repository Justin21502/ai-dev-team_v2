import os
import re

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


def write_files(files: dict[str, str], base_dir: str) -> list[str]:
    """Write parsed files to base_dir, creating subdirectories as needed."""
    written = []
    for rel_path, content in files.items():
        # guard against path traversal out of the workspace
        safe_path = os.path.normpath(rel_path).lstrip(os.sep)
        if safe_path.startswith(".."):
            continue
        full_path = os.path.join(base_dir, safe_path)
        os.makedirs(os.path.dirname(full_path) or base_dir, exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)
        written.append(full_path)
    return written


def read_files_as_text(paths: list[str]) -> str:
    """Concatenate files with headers, for feeding back to an agent as context."""
    chunks = []
    for path in paths:
        with open(path) as f:
            chunks.append(f"### FILE: {path}\n```\n{f.read()}\n```")
    return "\n\n".join(chunks)
