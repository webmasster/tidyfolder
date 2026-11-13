"""Command-line interface for tidyfolder."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from tidyfolder import __version__
from tidyfolder.config import (
    ConfigError,
    Settings,
    default_settings,
    discover_config,
    load_settings,
    merge_cli,
)
from tidyfolder.duplicates import find_duplicates, plan_duplicate_moves
from tidyfolder.organizer import OrganizeResult, apply_moves, organize, plan_moves
from tidyfolder.report import format_dupes, format_plan, format_undo
from tidyfolder.safety import UnsafePathError, resolve_target
from tidyfolder.undo import (
    UndoError,
    apply_undo,
    build_log,
    default_log_path,
    load_log,
    write_log,
)


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
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Also group files into YYYY-MM folders by modification time.",
    )
    organize_cmd.add_argument(
        "--recursive",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include files in subfolders, not only the top level.",
    )
    organize_cmd.add_argument(
        "--include-hidden",
        action=argparse.BooleanOptionalAction,
        default=None,
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
        "--config",
        metavar="PATH",
        help="TOML config file. Overrides the usual search path.",
    )
    organize_cmd.add_argument(
        "--force",
        action="store_true",
        help="Allow organizing the home directory or other protected paths.",
    )
    organize_cmd.add_argument(
        "--undo-log",
        metavar="PATH",
        help=(
            "Where to write the undo log. Defaults to "
            ".tidyfolder-undo.json inside the folder."
        ),
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
    undo.add_argument(
        "--log",
        metavar="PATH",
        help=(
            "Undo log to read. Defaults to .tidyfolder-undo.json "
            "inside the folder."
        ),
    )
    undo.add_argument(
        "--force",
        action="store_true",
        help="Restore files even if their contents have changed.",
    )

    dupes = sub.add_parser(
        "dupes",
        help="Find duplicate files by content hash.",
    )
    dupes.add_argument("path", help="Folder to scan.")
    dupes.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview extra copies that would be moved, if --move-to is set.",
    )
    dupes.add_argument(
        "--recursive",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include files in subfolders, not only the top level.",
    )
    dupes.add_argument(
        "--include-hidden",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include hidden files and files inside hidden folders.",
    )
    dupes.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help="Skip files matching this glob. May be repeated.",
    )
    dupes.add_argument(
        "--move-to",
        metavar="FOLDER",
        help=(
            "Move extra copies into this folder (created if needed). "
            "The original, oldest file is left in place. Nothing is deleted."
        ),
    )
    dupes.add_argument(
        "--force",
        action="store_true",
        help="Allow scanning the home directory or other protected paths.",
    )
    dupes.add_argument(
        "--config",
        metavar="PATH",
        help="TOML config file. Overrides the usual search path.",
    )

    categories = sub.add_parser(
        "categories",
        help="List the category names and extensions that would be used.",
    )
    categories.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Folder used to discover a local tidyfolder.toml (default: .).",
    )
    categories.add_argument(
        "--config",
        metavar="PATH",
        help="TOML config file. Overrides the usual search path.",
    )

    return parser


def _load_for(root: Path, explicit_config: Optional[str]) -> Settings:
    explicit = Path(explicit_config) if explicit_config else None
    found = discover_config(root, explicit)
    return load_settings(found) if found else default_settings()


def _print_result(result, *, verbose: bool) -> None:
    # format_plan already lists every move; --verbose is reserved for later
    # commands that hide detail by default.
    del verbose
    print(format_plan(result))


def _run_organize(args: argparse.Namespace) -> int:
    root = Path(args.path)
    try:
        # Resolve only for config discovery; organizer will resolve again
        # and apply safety checks.
        search_root = root.expanduser()
        if search_root.exists() and search_root.is_dir():
            search_root = search_root.resolve()
        settings = merge_cli(
            _load_for(search_root, args.config),
            by_date=args.by_date,
            include_hidden=args.include_hidden,
            recursive=args.recursive,
        )
        kwargs = dict(
            recursive=settings.recursive,
            include_hidden=settings.include_hidden,
            by_date=settings.by_date,
            excludes=args.exclude or None,
            categories=settings.categories,
            other_folder=settings.other_folder,
            force=args.force,
        )
        if args.dry_run:
            result = plan_moves(root, **kwargs)
            result.dry_run = True
        else:
            result = organize(root, **kwargs)
    except (UnsafePathError, ConfigError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    _print_result(result, verbose=args.verbose)
    if settings.config_path:
        print(f"Using config: {settings.config_path}")
    if not args.dry_run and result.moves:
        log_path = Path(args.undo_log) if args.undo_log else default_log_path(result.root)
        write_log(build_log(result.root, result.moves), log_path)
        print(
            f"Undo log written to {log_path}. "
            f"Run 'tidyfolder undo {result.root}' to revert."
        )
    return 0


def _run_undo(args: argparse.Namespace) -> int:
    try:
        root = resolve_target(Path(args.path))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    log_path = Path(args.log) if args.log else default_log_path(root)
    try:
        log = load_log(log_path)
        result = apply_undo(
            log,
            dry_run=args.dry_run,
            force=args.force,
            log_path=log_path,
        )
    except UndoError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(format_undo(result))
    return 0 if not result.skipped else 1


def _run_categories(args: argparse.Namespace) -> int:
    root = Path(args.path)
    try:
        search_root = root.expanduser()
        if search_root.exists() and search_root.is_dir():
            search_root = search_root.resolve()
        settings = _load_for(search_root, args.config)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if settings.config_path:
        print(f"Using config: {settings.config_path}")
    else:
        print("Using built-in categories.")
    print(f"Other folder: {settings.other_folder}")
    print()
    width = max(len(name) for name in settings.categories) if settings.categories else 0
    for name in settings.categories:
        exts = ", ".join(settings.categories[name])
        print(f"  {name:<{width}}  {exts}")
    return 0


def _run_dupes(args: argparse.Namespace) -> int:
    root = Path(args.path)
    try:
        search_root = root.expanduser()
        if search_root.exists() and search_root.is_dir():
            search_root = search_root.resolve()
        settings = merge_cli(
            _load_for(search_root, args.config),
            include_hidden=args.include_hidden,
            recursive=args.recursive,
        )
        result = find_duplicates(
            root,
            recursive=settings.recursive,
            include_hidden=settings.include_hidden,
            excludes=args.exclude or None,
            force=args.force,
        )
        if args.move_to:
            plan_duplicate_moves(result, Path(args.move_to))
            result.dry_run = args.dry_run
            if result.moves and not args.dry_run:
                applied = OrganizeResult(root=result.root, moves=result.moves)
                apply_moves(applied)
                result.moves = applied.moves
                log_path = default_log_path(result.root)
                if log_path.exists():
                    log_path = result.root / ".tidyfolder-dupes-undo.json"
                write_log(build_log(result.root, result.moves), log_path)
                print(format_dupes(result))
                print(
                    f"Undo log written to {log_path}. "
                    f"Run 'tidyfolder undo {result.root} --log {log_path}' to revert."
                )
                return 0
        else:
            result.dry_run = args.dry_run
        print(format_dupes(result))
        return 0
    except (UnsafePathError, ConfigError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "organize":
        return _run_organize(args)
    if args.command == "undo":
        return _run_undo(args)
    if args.command == "dupes":
        return _run_dupes(args)
    if args.command == "categories":
        return _run_categories(args)

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
