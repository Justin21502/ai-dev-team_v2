"""Simple hello world module."""

__all__ = ["hello"]


def hello() -> None:
    """Print 'Hello World' to standard output."""
    print("Hello World")


if __name__ == "__main__":
    hello()
