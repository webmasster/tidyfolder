"""Human-readable summaries of organize and undo plans."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from tidyfolder.organizer import OrganizeResult, PlannedMove


def relative_to_root(path: Path, root: Path) -> str:
    """Return a POSIX-style path relative to ``root`` when possible."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def group_by_category(moves: Sequence[PlannedMove]) -> List[Tuple[str, List[PlannedMove]]]:
    """Group moves by category, preserving first-seen category order."""
    grouped: dict[str, List[PlannedMove]] = defaultdict(list)
    order: List[str] = []
    for move in moves:
        if move.category not in grouped:
            order.append(move.category)
        grouped[move.category].append(move)
    return [(name, grouped[name]) for name in order]


def format_plan(result: OrganizeResult, *, verb: str | None = None) -> str:
    """Return a multi-line preview of planned or applied moves.

    ``verb`` defaults to ``Would move`` for dry runs and ``Moved`` otherwise.
    """
    if verb is None:
        verb = "Would move" if result.dry_run else "Moved"

    if not result.moves:
        lines = ["Nothing to do. The folder is already organized, or it is empty."]
        if result.skipped:
            lines.append(f"Skipped {result.skipped} file(s) already in place.")
        return "\n".join(lines)

    heading = "Planned moves (dry run):" if result.dry_run else "Applied moves:"
    lines: List[str] = [heading, ""]

    for category, moves in group_by_category(result.moves):
        lines.append(f"{category} ({len(moves)})")
        width = max(len(move.source.name) for move in moves)
        for move in moves:
            src = move.source.name
            dest = relative_to_root(move.destination, result.root)
            lines.append(f"  {src:<{width}}  ->  {dest}")
        lines.append("")

    lines.append(f"{verb} {len(result.moves)} file(s).")
    if result.skipped:
        lines.append(f"Skipped {result.skipped} file(s) already in place.")
    if result.dry_run and result.moves:
        lines.append("Dry run only. Re-run without --dry-run to apply these moves.")
    return "\n".join(lines)
