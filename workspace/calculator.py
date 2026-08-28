"""
Simple arithmetic library.

Provides basic operations: addition, subtraction, multiplication, and division.
All functions accept `int` or `float` and return a `float` (except addition,
subtraction, and multiplication which preserve the input type when possible).

A custom `DivisionByZeroError` is raised for division by zero to allow
clearer error handling in the CLI.
"""

from __future__ import annotations

from typing import Union

Number = Union[int, float]


class DivisionByZeroError(ZeroDivisionError):
    """Raised when an attempt is made to divide by zero."""
    pass


def _validate_number(value: object, name: str) -> Number:
    """
    Ensure that ``value`` is an ``int`` or ``float`` (but not ``bool``).

    Parameters
    ----------
    value : object
        The value to validate.
    name : str
        The name of the argument (used in the error message).

    Returns
    -------
    Number
        The original value, typed as ``Number``.

    Raises
    ------
    TypeError
        If ``value`` is not an ``int`` or ``float`` (or is a ``bool``).
    """
    # ``bool`` is a subclass of ``int``; we explicitly reject it to avoid
    # surprising behaviour (e.g. True + 1 == 2).
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be int or float, got {type(value).__name__}")
    return value  # type: ignore[return-value]


def add(a: Number, b: Number) -> Number:
    """
    Return the sum of ``a`` and ``b``.

    Parameters
    ----------
    a, b : int or float
        Operands to be added.

    Returns
    -------
    int or float
        The arithmetic sum.
    """
    a = _validate_number(a, "a")
    b = _validate_number(b, "b")
    return a + b


def sub(a: Number, b: Number) -> Number:
    """
    Return the difference of ``a`` and ``b`` (``a - b``).

    Parameters
    ----------
    a, b : int or float
        Operands where ``b`` is subtracted from ``a``.

    Returns
    -------
    int or float
        The arithmetic difference.
    """
    a = _validate_number(a, "a")
    b = _validate_number(b, "b")
    return a - b


def mul(a: Number, b: Number) -> Number:
    """
    Return the product of ``a`` and ``b``.

    Parameters
    ----------
    a, b : int or float
        Operands to be multiplied.

    Returns
    -------
    int or float
        The arithmetic product.
    """
    a = _validate_number(a, "a")
    b = _validate_number(b, "b")
    return a * b


def div(a: Number, b: Number) -> float:
    """
    Return the quotient of ``a`` divided by ``b`` (``a / b``).

    Parameters
    ----------
    a, b : int or float
        Operands where ``a`` is divided by ``b``.

    Returns
    -------
    float
        The arithmetic quotient.

    Raises
    ------
    DivisionByZeroError
        If ``b`` is zero.
    TypeError
        If either ``a`` or ``b`` is not a number.
    """
    a = _validate_number(a, "a")
    b = _validate_number(b, "b")
    if b == 0:
        raise DivisionByZeroError("division by zero")
    return a / b


__all__ = ["add", "sub", "mul", "div", "DivisionByZeroError"]
