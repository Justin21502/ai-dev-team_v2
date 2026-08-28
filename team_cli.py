"""Cross-platform command-line interface for AI Dev Team."""

from __future__ import annotations

import argparse
import sys

from orchestrator import run_team
from team_config import get_config
from team_config_cli import show_config, show_models
from team_doctor import run_doctor
from team_history import show_history, show_run, show_status
from team_replay import show_replay
from team_version import get_version, show_version


def _positive_run_number(value: str) -> int:
    """Parse a positive run number for history/replay commands."""
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid run number: {value}"
        ) from exc

    if number < 1:
        raise argparse.ArgumentTypeError(
            "run number must be greater than zero"
        )

    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="team",
        description="AI Dev Team",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"AI Dev Team v{get_version()}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        metavar="COMMAND",
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Run the AI development team.",
    )
    run_parser.add_argument(
        "task",
        nargs=argparse.REMAINDER,
        help="Task for the team to build.",
    )

    subparsers.add_parser(
        "status",
        help="Show the latest team status.",
    )

    history_parser = subparsers.add_parser(
        "history",
        help="Show run history or one run.",
    )
    history_parser.add_argument(
        "run_number",
        nargs="?",
        type=_positive_run_number,
    )

    replay_parser = subparsers.add_parser(
        "replay",
        help="Replay a saved team run.",
    )
    replay_parser.add_argument(
        "run_number",
        type=_positive_run_number,
    )

    subparsers.add_parser(
        "doctor",
        help="Check the local AI Dev Team installation.",
    )

    subparsers.add_parser(
        "config",
        help="Show resolved configuration.",
    )

    subparsers.add_parser(
        "models",
        help="Show configured model routing.",
    )

    subparsers.add_parser(
        "version",
        help="Show the AI Dev Team version.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "run":
        task = " ".join(args.task).strip()

        if not task:
            task = input(
                "Describe what you want the team to build: "
            ).strip()

        if not task:
            print(
                "A task description is required.",
                file=sys.stderr,
            )
            return 2

        run_team(task)

        config = get_config()

        print(
            "Done. See "
            f"{config.workspace_dir} "
            "for the generated project and "
            f"{config.run_log_path} "
            "for the latest transcript."
        )

        return 0

    if args.command == "status":
        show_status()
        return 0

    if args.command == "history":
        if args.run_number is None:
            show_history()
        else:
            show_run(args.run_number)

        return 0

    if args.command == "replay":
        show_replay(args.run_number)
        return 0

    if args.command == "doctor":
        return run_doctor()

    if args.command == "config":
        show_config()
        return 0

    if args.command == "models":
        show_models()
        return 0

    if args.command == "version":
        show_version()
        return 0

    parser.error(
        f"unsupported command: {args.command}"
    )

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
