"""Command‑line interface for the temperature_converter package."""

from __future__ import annotations

import argparse
import sys
from importlib import metadata

from .core import TemperatureConverter


def _get_version() -> str:
    """Retrieve the package version from metadata."""
    try:
        return metadata.version("temperature_converter")
    except metadata.PackageNotFoundError:
        # Fallback for editable installs where metadata may not be present yet.
        return "0.0.0"


def build_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="temp-convert",
        description="Convert temperatures between Celsius and Fahrenheit.",
    )
    parser.add_argument(
        "-t",
        "--temperature",
        type=float,
        required=True,
        help="Numeric temperature value to convert.",
    )
    parser.add_argument(
        "-f",
        "--from-unit",
        type=str.upper,
        choices=["C", "F"],
        required=True,
        help="Unit of the input temperature (C or F).",
    )
    parser.add_argument(
        "-o",
        "--to-unit",
        type=str.upper,
        choices=["C", "F"],
        required=True,
        help="Desired output unit (C or F).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_get_version()}",
        help="Show program's version number and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for the console script."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = TemperatureConverter.convert(
            value=args.temperature,
            from_unit=args.from_unit,
            to_unit=args.to_unit,
        )
    except ValueError as exc:
        parser.error(str(exc))

    unit_symbol = "°C" if args.to_unit == "C" else "°F"
    # Two decimal places provide a clean, readable output.
    print(f"{result:.2f} {unit_symbol}")


if __name__ == "__main__":
    # When executed directly, forward sys.argv[1:] to ``main``.
    main(sys.argv[1:])
