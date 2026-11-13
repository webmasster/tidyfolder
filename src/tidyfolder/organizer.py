"""Plan and apply file moves into category subfolders."""

from __future__ import annotations

import datetime
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set

from tidyfolder.categories import (
    DEFAULT_CATEGORIES,
    DEFAULT_OTHER_FOLDER,
    build_extension_map,
    category_for,
)
from tidyfolder.safety import (
    UnsafePathError,
    is_dangerous_target,
    resolve_target,
    should_skip,
)


@dataclass
class PlannedMove:
    """A single file move that has been planned but may not be applied yet."""

    source: Path
    destination: Path
    category: str


@dataclass
class OrganizeResult:
    """Summary of an organize run."""

    root: Path
    moves: List[PlannedMove] = field(default_factory=list)
    skipped: int = 0
    applied: int = 0
    dry_run: bool = False


def collect_files(
    root: Path,
    *,
    recursive: bool = False,
    include_hidden: bool = False,
    excludes: Optional[Iterable[str]] = None,
) -> List[Path]:
    """Return files under ``root`` that are candidates for organizing."""
    if recursive:
        candidates = [p for p in sorted(root.rglob("*")) if not p.is_dir()]
    else:
        candidates = [p for p in sorted(root.iterdir()) if p.is_file()]

    kept: List[Path] = []
    for path in candidates:
        if should_skip(
            path,
            root,
            include_hidden=include_hidden,
            extra_excludes=excludes,
        ):
            continue
        kept.append(path)
    return kept


def already_organized(path: Path, root: Path, category: str, by_date: bool) -> bool:
    """Return True if ``path`` already lives in its category (and date) folder."""
    try:
        relative = path.parent.relative_to(root)
    except ValueError:
        return False
    parts = relative.parts
    if not parts or parts[0] != category:
        return False
    if by_date:
        # Expect Category/YYYY-MM/...
        return len(parts) >= 2
    return True


def date_folder(path: Path) -> str:
    """Return a YYYY-MM folder name from the file's modification time."""
    mtime = path.stat().st_mtime
    return datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m")


def next_free_path(path: Path, reserved: Set[Path]) -> Path:
    """Return a path that does not exist and is not already reserved.

    If ``photo.jpg`` is taken, try ``photo_1.jpg``, ``photo_2.jpg``, and so on.
    Never overwrites an existing file.
    """
    if not path.exists() and path not in reserved:
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    n = 1
    while True:
        candidate = parent / f"{stem}_{n}{suffix}"
        if not candidate.exists() and candidate not in reserved:
            return candidate
        n += 1


def plan_moves(
    root: Path,
    *,
    recursive: bool = False,
    include_hidden: bool = False,
    by_date: bool = False,
    excludes: Optional[Iterable[str]] = None,
    categories: Optional[Mapping[str, Sequence[str]]] = None,
    other_folder: str = DEFAULT_OTHER_FOLDER,
    force: bool = False,
) -> OrganizeResult:
    """Compute destination paths without changing any files."""
    resolved = resolve_target(root)
    if is_dangerous_target(resolved) and not force:
        raise UnsafePathError(
            f"refusing to organize {resolved} because it looks like a system "
            "or home directory. Pass --force if you are sure."
        )

    mapping = build_extension_map(categories or DEFAULT_CATEGORIES)
    files = collect_files(
        resolved,
        recursive=recursive,
        include_hidden=include_hidden,
        excludes=excludes,
    )

    result = OrganizeResult(root=resolved)
    reserved: Set[Path] = set()

    for path in files:
        category = category_for(path.name, mapping, other_folder)
        if already_organized(path, resolved, category, by_date):
            result.skipped += 1
            continue

        dest_dir = resolved / category
        if by_date:
            dest_dir = dest_dir / date_folder(path)
        destination = next_free_path(dest_dir / path.name, reserved)
        reserved.add(destination)
        result.moves.append(
            PlannedMove(source=path, destination=destination, category=category)
        )

    return result


def apply_moves(result: OrganizeResult) -> OrganizeResult:
    """Create destination folders and move files. Never overwrites."""
    reserved: Set[Path] = set()
    for move in result.moves:
        move.destination.parent.mkdir(parents=True, exist_ok=True)
        dest = next_free_path(move.destination, reserved)
        shutil.move(str(move.source), str(dest))
        move.destination = dest
        reserved.add(dest)
        result.applied += 1
    return result


def organize(
    root: Path,
    *,
    recursive: bool = False,
    include_hidden: bool = False,
    by_date: bool = False,
    excludes: Optional[Iterable[str]] = None,
    categories: Optional[Mapping[str, Sequence[str]]] = None,
    other_folder: str = DEFAULT_OTHER_FOLDER,
    force: bool = False,
) -> OrganizeResult:
    """Plan and apply an organize run."""
    result = plan_moves(
        root,
        recursive=recursive,
        include_hidden=include_hidden,
        by_date=by_date,
        excludes=excludes,
        categories=categories,
        other_folder=other_folder,
        force=force,
    )
    return apply_moves(result)
