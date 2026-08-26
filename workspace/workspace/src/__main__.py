"""Entry point for the hello world package.

Running `python -m src` will execute this module and print the greeting.
"""

from .hello import greet


def main() -> None:
    """Print the greeting to standard output."""
    print(greet())


if __name__ == "__main__":
    main()
