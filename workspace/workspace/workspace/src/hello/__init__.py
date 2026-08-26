"""
Deprecated package version of the Hello World module.

This package was introduced by mistake and should not be used.
The functional implementation resides in `workspace/src/hello.py`.

Attempting to import from this package will raise an informative error.
"""

def __getattr__(name):
    raise ImportError(
        "The `hello` package under `workspace/workspace/src` is deprecated. "
        "Please import the `hello` function from the top‑level module "
        "`workspace/src/hello.py` instead."
    )
