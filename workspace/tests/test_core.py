"""Unit tests for temperature_converter.core."""

import math
import pytest

from temperature_converter.core import TemperatureConverter


@pytest.mark.parametrize(
    "celsius, expected_fahrenheit",
    [
        (0, 32),
        (100, 212),
        (-40, -40),
        (37, 98.6),
    ],
)
def test_celsius_to_fahrenheit(celsius, expected_fahrenheit):
    assert math.isclose(
        TemperatureConverter.celsius_to_fahrenheit(celsius),
        expected_fahrenheit,
        rel_tol=1e-9,
    )


@pytest.mark.parametrize(
    "fahrenheit, expected_celsius",
    [
        (32, 0),
        (212, 100),
        (-40, -40),
        (98.6, 37),
    ],
)
def test_fahrenheit_to_celsius(fahrenheit, expected_celsius):
    assert math.isclose(
        TemperatureConverter.fahrenheit_to_celsius(fahrenheit),
        expected_celsius,
        rel_tol=1e-9,
    )


@pytest.mark.parametrize(
    "value, from_u, to_u, expected",
    [
        (0, "C", "F", 32),
        (100, "C", "F", 212),
        (-40, "F", "C", -40),
        (212, "F", "C", 100),
        (25, "C", "C", 25),  # identity conversion
        (77, "F", "F", 77),
    ],
)
def test_convert_basic(value, from_u, to_u, expected):
    result = TemperatureConverter.convert(value, from_u, to_u)
    assert math.isclose(result, expected, rel_tol=1e-9)


def test_convert_case_insensitivity():
    assert TemperatureConverter.convert(0, "c", "f") == 32
    assert TemperatureConverter.convert(32, "F", "c") == 0


def test_convert_invalid_units():
    with pytest.raises(ValueError, match="Unsupported source unit"):
        TemperatureConverter.convert(10, "K", "C")
    with pytest.raises(ValueError, match="Unsupported target unit"):
        TemperatureConverter.convert(10, "C", "X")


def test_convert_non_finite():
    with pytest.raises(ValueError, match="finite"):
        TemperatureConverter.convert(float("inf"), "C", "F")
    with pytest.raises(ValueError, match="finite"):
        TemperatureConverter.convert(float("-nan"), "F", "C")
