"""Human-readable summaries of organize and undo plans."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

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


def format_plan(result: OrganizeResult, *, verb: Optional[str] = None) -> str:
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


def format_undo(result: "UndoResult") -> str:
    """Return a multi-line preview of an undo run."""
    verb = "Would restore" if result.dry_run else "Restored"
    heading = "Planned undo (dry run):" if result.dry_run else "Undo applied:"
    lines: List[str] = []

    if not result.restored and not result.skipped:
        return "Nothing to undo. The undo log has no recorded moves."

    if result.restored:
        lines.append(heading)
        lines.append("")
        width = max(
            len(relative_to_root(item.destination, result.root))
            for item in result.restored
        )
        for item in result.restored:
            src = relative_to_root(item.destination, result.root)
            dest = relative_to_root(item.source, result.root)
            lines.append(f"  {src:<{width}}  ->  {dest}")
        lines.append("")
        lines.append(f"{verb} {len(result.restored)} file(s).")

    for warning in result.skipped:
        lines.append(f"Skipped: {warning}")

    if result.dry_run and result.restored:
        lines.append("Dry run only. Re-run without --dry-run to apply this undo.")
    return "\n".join(lines)



def format_dupes(result: "DuplicateResult") -> str:
    """Return a multi-line report of duplicate groups and optional moves."""
    lines: List[str] = []
    if not result.groups:
        return f"No duplicates found. Scanned {result.scanned} file(s)."

    lines.append(
        f"Found {len(result.groups)} duplicate group(s) "
        f"in {result.scanned} file(s):"
    )
    lines.append("")
    for index, group in enumerate(result.groups, start=1):
        extra_count = len(group.extras)
        size = group.size
        if size >= 1024 * 1024:
            size_label = f"{size / (1024 * 1024):.1f} MiB"
        elif size >= 1024:
            size_label = f"{size / 1024:.1f} KiB"
        else:
            size_label = f"{size} bytes"
        empty = " (empty file)" if size == 0 else ""
        lines.append(
            f"Group {index}: {extra_count + 1} copies, {size_label}{empty}, "
            f"sha256={group.sha256[:12]}..."
        )
        lines.append(f"  keep   {relative_to_root(group.files[0], result.root)}")
        for extra in group.extras:
            lines.append(f"  extra  {relative_to_root(extra, result.root)}")
        lines.append("")

    wasted = sum(group.size * len(group.extras) for group in result.groups)
    lines.append(f"Wasted space: {wasted} byte(s) in extra copies.")

    if result.moves:
        verb = "Would move" if result.dry_run else "Moved"
        dest = relative_to_root(result.move_to, result.root) if result.move_to else "Duplicates"
        lines.append("")
        lines.append(f"{verb} {len(result.moves)} extra copy(ies) to {dest}/.")
        if result.dry_run:
            lines.append("Dry run only. Re-run without --dry-run to apply these moves.")
    return "\n".join(lines)
