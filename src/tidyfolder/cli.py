"""Command-line interface for tidyfolder."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from tidyfolder import __version__
from tidyfolder.organizer import organize, plan_moves
from tidyfolder.report import format_plan
from tidyfolder.safety import UnsafePathError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tidyfolder",
        description=(
            "Safely organize a messy folder into subfolders by file type "
            "and optional date, with dry-run preview and undo."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"tidyfolder {__version__}",
    )
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    organize_cmd = sub.add_parser(
        "organize",
        help="Move files into category (and optional date) subfolders.",
    )
    organize_cmd.add_argument("path", help="Folder to organize.")
    organize_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview planned moves without changing anything.",
    )
    organize_cmd.add_argument(
        "--by-date",
        action="store_true",
        help="Also group files into YYYY-MM folders by modification time.",
    )
    organize_cmd.add_argument(
        "--recursive",
        action="store_true",
        help="Include files in subfolders, not only the top level.",
    )
    organize_cmd.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and files inside hidden folders.",
    )
    organize_cmd.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help="Skip files matching this glob. May be repeated.",
    )
    organize_cmd.add_argument(
        "--force",
        action="store_true",
        help="Allow organizing the home directory or other protected paths.",
    )
    organize_cmd.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print every planned or applied move.",
    )

    undo = sub.add_parser("undo", help="Revert the last organize run.")
    undo.add_argument("path", help="Folder that was organized.")
    undo.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview planned reversals without changing anything.",
    )

    return parser


def _print_result(result, *, verbose: bool) -> None:
    # format_plan already lists every move; --verbose is reserved for later
    # commands that hide detail by default.
    del verbose
    print(format_plan(result))


def _run_organize(args: argparse.Namespace) -> int:
    root = Path(args.path)
    try:
        if args.dry_run:
            result = plan_moves(
                root,
                recursive=args.recursive,
                include_hidden=args.include_hidden,
                by_date=args.by_date,
                excludes=args.exclude or None,
                force=args.force,
            )
            result.dry_run = True
        else:
            result = organize(
                root,
                recursive=args.recursive,
                include_hidden=args.include_hidden,
                by_date=args.by_date,
                excludes=args.exclude or None,
                force=args.force,
            )
    except UnsafePathError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    _print_result(result, verbose=args.verbose)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "organize":
        return _run_organize(args)
    if args.command == "undo":
        print(
            f"undo is not implemented yet (path={args.path!r}, "
            f"dry_run={args.dry_run}).",
            file=sys.stderr,
        )
        return 2

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
