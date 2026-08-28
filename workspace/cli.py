"""
Command‑line interface for the simple calculator.

Provides both an interactive menu and a non‑interactive mode using
command‑line arguments. The core arithmetic logic lives in `calculator.py`.
"""

from __future__ import annotations

import argparse
import sys

from calculator import add, sub, mul, div, DivisionByZeroError


def _prompt_float(prompt: str) -> float:
    """Prompt the user for a number, repeating until a valid float is entered."""
    while True:
        try:
            value = input(prompt)
            return float(value)
        except ValueError:
            print("Invalid number, please try again.")


def _print_menu() -> None:
    """Display the operation menu."""
    print("\nSimple Calculator")
    print("-----------------")
    print("1) Add")
    print("2) Subtract")
    print("3) Multiply")
    print("4) Divide")
    print("0) Exit")


def _handle_choice(choice: str) -> bool:
    """
    Execute the operation corresponding to `choice`.

    Returns
    -------
    bool
        True if the loop should continue, False to exit.
    """
    if choice == "0":
        print("Goodbye!")
        return False

    if choice not in {"1", "2", "3", "4"}:
        print("Invalid choice, please select a valid option.")
        return True

    a = _prompt_float("Enter the first number: ")
    b = _prompt_float("Enter the second number: ")

    try:
        if choice == "1":
            result = add(a, b)
            op = "+"
        elif choice == "2":
            result = sub(a, b)
            op = "-"
        elif choice == "3":
            result = mul(a, b)
            op = "*"
        else:  # choice == "4"
            result = div(a, b)
            op = "/"
        print(f"{a} {op} {b} = {result}")
    except DivisionByZeroError:
        print("Error: cannot divide by zero.")
    return True


def _run_interactive() -> None:
    """Run the interactive calculator loop."""
    try:
        while True:
            _print_menu()
            choice = input("Select an option: ").strip()
            if not _handle_choice(choice):
                break
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
        sys.exit(0)


def _run_cli(args: argparse.Namespace) -> None:
    """Execute a single calculation based on parsed CLI arguments."""
    operation_map = {
        "add": (add, "+"),
        "sub": (sub, "-"),
        "mul": (mul, "*"),
        "div": (div, "/"),
    }
    func, symbol = operation_map[args.operation]
    try:
        result = func(args.a, args.b)
        print(f"{args.a} {symbol} {args.b} = {result}")
    except DivisionByZeroError:
        print("Error: cannot divide by zero.", file=sys.stderr)
        sys.exit(1)


def _build_parser() -> argparse.ArgumentParser:
    """Create the top‑level argument parser."""
    parser = argparse.ArgumentParser(
        description="Simple command‑line calculator."
    )
    parser.add_argument(
        "operation",
        nargs="?",
        choices=["add", "sub", "mul", "div"],
        help="Arithmetic operation to perform.",
    )
    parser.add_argument(
        "a",
        nargs="?",
        type=float,
        help="First operand (float).",
    )
    parser.add_argument(
        "b",
        nargs="?",
        type=float,
        help="Second operand (float).",
    )
    return parser


def main() -> None:
    """Entry point for the calculator."""
    parser = _build_parser()
    args = parser.parse_args()

    # If all three positional arguments are provided, run in CLI mode.
    if args.operation and args.a is not None and args.b is not None:
        _run_cli(args)
    else:
        # Fallback to interactive mode.
        _run_interactive()


if __name__ == "__main__":
    main()
