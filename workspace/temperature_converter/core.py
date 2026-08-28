"""Core conversion logic for temperature values.

Provides a small, pure‑Python API that can be used programmatically
or from the command‑line interface.
"""

from __future__ import annotations

import math
from typing import Final, Union

Number = Union[int, float]

__all__ = ["TemperatureConverter"]


class TemperatureConverter:
    """Utility class offering temperature conversion methods."""

    _VALID_UNITS: Final[set[str]] = {"C", "F"}

    @staticmethod
    def _validate_number(value: Number) -> None:
        """Validate that *value* is a finite number.

        Args:
            value: The value to validate.

        Raises:
            ValueError: If *value* is not a finite int or float.
        """
        if not isinstance(value, (int, float)):
            raise ValueError("Temperature must be a numeric type.")
        if not math.isfinite(value):
            raise ValueError("Temperature must be a finite number.")

    @staticmethod
    def celsius_to_fahrenheit(celsius: Number) -> float:
        """Convert Celsius to Fahrenheit.

        Args:
            celsius: Temperature in degrees Celsius.

        Returns:
            Temperature in degrees Fahrenheit.

        Raises:
            ValueError: If *celsius* is not a finite number.
        """
        TemperatureConverter._validate_number(celsius)
        return (celsius * 9.0 / 5.0) + 32.0

    @staticmethod
    def fahrenheit_to_celsius(fahrenheit: Number) -> float:
        """Convert Fahrenheit to Celsius.

        Args:
            fahrenheit: Temperature in degrees Fahrenheit.

        Returns:
            Temperature in degrees Celsius.

        Raises:
            ValueError: If *fahrenheit* is not a finite number.
        """
        TemperatureConverter._validate_number(fahrenheit)
        return (fahrenheit - 32.0) * 5.0 / 9.0

    @classmethod
    def convert(cls, value: Number, from_unit: str, to_unit: str) -> float:
        """Convert a temperature from one unit to another.

        Supported units are Celsius (``C``) and Fahrenheit (``F``).  The
        comparison is case‑insensitive.

        Args:
            value: The numeric temperature to convert.
            from_unit: Source unit, ``'C'`` or ``'F'``.
            to_unit: Target unit, ``'C'`` or ``'F'``.

        Returns:
            The converted temperature.

        Raises:
            ValueError: If either unit is unsupported or the value is not
                a finite number.
        """
        cls._validate_number(value)

        from_u = from_unit.upper()
        to_u = to_unit.upper()

        if from_u not in cls._VALID_UNITS:
            raise ValueError(f"Unsupported source unit: {from_unit!r}")
        if to_u not in cls._VALID_UNITS:
            raise ValueError(f"Unsupported target unit: {to_unit!r}")

        if from_u == to_u:
            return float(value)

        if from_u == "C" and to_u == "F":
            return cls.celsius_to_fahrenheit(value)
        if from_u == "F" and to_u == "C":
            return cls.fahrenheit_to_celsius(value)

        # This point should never be reached because all combos are covered.
        raise ValueError(f"Conversion from {from_unit!r} to {to_unit!r} is not supported.")
