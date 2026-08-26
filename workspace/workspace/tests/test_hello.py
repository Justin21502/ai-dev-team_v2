import pytest
from hello import hello


def test_hello_output(capsys):
    """Ensure that `hello()` prints the expected message."""
    hello()
    captured = capsys.readouterr()
    assert captured.out == "Hello, World!\n"


@pytest.mark.parametrize(
    "expected",
    ["Hello, World!"],
)
def test_hello_message(expected, capsys):
    """Parametrized version demonstrating pytest features."""
    hello()
    out, _ = capsys.readouterr()
    assert out.strip() == expected


def test_hello_no_error():
    """Calling `hello()` should not raise any exception."""
    hello()
