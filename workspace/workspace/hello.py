"""Compatibility module for legacy imports.

This module provides a `hello` function that returns the greeting string.
It mirrors the functionality of `src.hello.greet` to maintain backward
compatibility with tests or scripts that import `hello` directly from the
project root.
"""

def hello() -> str:
    """Return the greeting string."""
    return "Hello World"
