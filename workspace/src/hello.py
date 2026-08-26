"""Simple hello world module."""

def greet() -> str:
    """Return the greeting string."""
    return "Hello World"


if __name__ == "__main__":
    # When executed directly, print the greeting.
    print(greet())
