"""Top‑level entry point for the Hello World function.

This module re‑exports the `hello` function defined in the source package
located at `src/hello.py`. It exists so that test modules can simply use:

    from hello import hello

without needing to know the internal package layout.
"""

from pathlib import Path
import importlib.util
import sys

# Resolve the path to the actual implementation module.
_src_dir = Path(__file__).parent / "src"
_impl_path = _src_dir / "hello.py"

if not _impl_path.is_file():
    raise ImportError(
        f"Cannot locate the implementation module at expected path: {_impl_path}"
    )

# Load the implementation module dynamically.
_spec = importlib.util.spec_from_file_location("hello_impl", _impl_path)
_impl = importlib.util.module_from_spec(_spec)  # type: ignore
assert _spec and _spec.loader  # for mypy/static check
_spec.loader.exec_module(_impl)  # type: ignore

# Re‑export the `hello` function.
hello = _impl.hello  # type: ignore

__all__ = ["hello"]
