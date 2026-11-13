"""Find duplicate files by SHA-256 and optionally set extras aside."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set

from tidyfolder.hashing import file_sha256
from tidyfolder.organizer import PlannedMove, collect_files, next_free_path
from tidyfolder.safety import UnsafePathError, is_dangerous_target, resolve_target


@dataclass
class DuplicateGroup:
    """A set of files that have the same content hash."""

    sha256: str
    size: int
    files: List[Path]  # the first entry is the one we keep

    @property
    def extras(self) -> List[Path]:
        return self.files[1:]


@dataclass
class DuplicateResult:
    """Summary of a duplicate scan, with optional planned moves."""

    root: Path
    groups: List[DuplicateGroup] = field(default_factory=list)
    moves: List[PlannedMove] = field(default_factory=list)
    scanned: int = 0
    dry_run: bool = False
    move_to: Optional[Path] = None


def _keeper(files: Sequence[Path]) -> List[Path]:
    """Put the oldest, then shortest-path, file first so we keep a stable original."""
    return sorted(files, key=lambda path: (path.stat().st_mtime, len(str(path)), str(path)))


def find_duplicates(
    root: Path,
    *,
    recursive: bool = False,
    include_hidden: bool = False,
    excludes: Optional[Iterable[str]] = None,
    force: bool = False,
) -> DuplicateResult:
    """Scan ``root`` and group files that share the same SHA-256 digest."""
    resolved = resolve_target(root)
    if is_dangerous_target(resolved) and not force:
        raise UnsafePathError(
            f"refusing to scan {resolved} because it looks like a system "
            "or home directory. Pass --force if you are sure."
        )
    files = collect_files(
        resolved,
        recursive=recursive,
        include_hidden=include_hidden,
        excludes=excludes,
    )
    by_hash: Dict[str, List[Path]] = {}
    sizes: Dict[str, int] = {}
    for path in files:
        digest = file_sha256(path)
        by_hash.setdefault(digest, []).append(path)
        sizes[digest] = path.stat().st_size

    groups = []
    for digest, paths in by_hash.items():
        if len(paths) < 2:
            continue
        groups.append(
            DuplicateGroup(sha256=digest, size=sizes[digest], files=_keeper(paths))
        )
    groups.sort(key=lambda group: (-group.size, group.sha256))
    return DuplicateResult(root=resolved, groups=groups, scanned=len(files))


def plan_duplicate_moves(
    result: DuplicateResult,
    destination: Path,
) -> DuplicateResult:
    """Plan moving every extra copy into ``destination`` (relative to root if needed)."""
    dest_dir = destination if destination.is_absolute() else result.root / destination
    reserved: Set[Path] = set()
    moves: List[PlannedMove] = []
    for group in result.groups:
        for extra in group.extras:
            target = next_free_path(dest_dir / extra.name, reserved)
            reserved.add(target)
            moves.append(
                PlannedMove(source=extra, destination=target, category=dest_dir.name)
            )
    result.moves = moves
    result.move_to = dest_dir
    return result
