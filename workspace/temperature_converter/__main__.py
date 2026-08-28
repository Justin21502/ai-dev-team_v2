"""Entry point for ``python -m temperature_converter``."""

from .cli import main

if __name__ == "__main__":
    # Forward the command‑line arguments (excluding the module name) to the CLI.
    import sys

    main(sys.argv[1:])
