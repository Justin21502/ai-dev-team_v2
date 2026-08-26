"""Tests for the hello module."""

from src.hello import greet


def test_greet():
    """The greet function should return 'Hello World'."""
    assert greet() == "Hello World"
