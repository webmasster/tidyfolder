"""Command-line interface for tidyfolder."""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from tidyfolder import __version__


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

    organize = sub.add_parser(
        "organize",
        help="Move files into category (and optional date) subfolders.",
    )
    organize.add_argument("path", help="Folder to organize.")
    organize.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview planned moves without changing anything.",
    )

    undo = sub.add_parser("undo", help="Revert the last organize run.")
    undo.add_argument("path", help="Folder that was organized.")
    undo.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview planned reversals without changing anything.",
    )

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "organize":
        print(
            f"organize is not implemented yet (path={args.path!r}, "
            f"dry_run={args.dry_run}).",
            file=sys.stderr,
        )
        return 2
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
