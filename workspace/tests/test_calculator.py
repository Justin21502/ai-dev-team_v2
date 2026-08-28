import pytest
from calculator import add, sub, mul, div, DivisionByZeroError


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (1, 2, 3),
        (-1, -5, -6),
        (3.5, 2.5, 6.0),
        (1000000, 2345678, 3345678),
        (0, 0, 0),
    ],
)
def test_add(a, b, expected):
    assert add(a, b) == expected


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (5, 3, 2),
        (-2, -4, 2),
        (10.5, 0.5, 10.0),
        (0, 100, -100),
        (-5, 5, -10),
    ],
)
def test_sub(a, b, expected):
    assert sub(a, b) == expected


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (2, 3, 6),
        (-1, 5, -5),
        (0, 100, 0),
        (3.5, 2, 7.0),
        (-2, -2, 4),
    ],
)
def test_mul(a, b, expected):
    assert mul(a, b) == expected


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (6, 3, 2.0),
        (5, 2, 2.5),
        (-9, 3, -3.0),
        (7, -2, -3.5),
        (10, 4, 2.5),
    ],
)
def test_div(a, b, expected):
    assert div(a, b) == pytest.approx(expected)


def test_division_by_zero():
    with pytest.raises(DivisionByZeroError):
        div(10, 0)


@pytest.mark.parametrize(
    "func, args",
    [
        (add, ("a", 1)),
        (sub, (2, "b")),
        (mul, ("x", "y")),
        (div, (5, "z")),
    ],
)
def test_invalid_type_raises_type_error(func, args):
    with pytest.raises(TypeError):
        func(*args)
