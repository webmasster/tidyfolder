"""JSON undo log: record applied moves and put files back."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

from tidyfolder.hashing import file_sha256
from tidyfolder.organizer import PlannedMove
from tidyfolder.safety import unique_destination

UNDO_LOG_NAME = ".tidyfolder-undo.json"
LOG_VERSION = 1


class UndoError(ValueError):
    """Raised when an undo log is missing, invalid, or cannot be applied safely."""


@dataclass
class LoggedMove:
    """One recorded move from an undo log."""

    source: Path  # original location
    destination: Path  # where the file was moved
    sha256: Optional[str] = None


@dataclass
class UndoLog:
    """In-memory representation of a tidyfolder undo log."""

    root: Path
    created_at: str
    moves: List[LoggedMove] = field(default_factory=list)
    version: int = LOG_VERSION
    tool: str = "tidyfolder"


@dataclass
class UndoResult:
    """Summary of an undo run."""

    root: Path
    log_path: Path
    restored: List[LoggedMove] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    dry_run: bool = False


def default_log_path(root: Path) -> Path:
    """Return the default undo-log path inside ``root``."""
    return root / UNDO_LOG_NAME


def build_log(root: Path, moves: Sequence[PlannedMove], *, hash_files: bool = True) -> UndoLog:
    """Build an undo log from applied (or about-to-be-applied) moves."""
    logged: List[LoggedMove] = []
    for move in moves:
        digest = file_sha256(move.destination if move.destination.exists() else move.source)
        if not hash_files:
            digest = None
        logged.append(
            LoggedMove(
                source=move.source,
                destination=move.destination,
                sha256=digest,
            )
        )
    return UndoLog(
        root=root,
        created_at=datetime.now(timezone.utc).isoformat(),
        moves=logged,
    )


def log_to_dict(log: UndoLog) -> Dict[str, Any]:
    """Serialize an :class:`UndoLog` to a JSON-compatible dict."""
    return {
        "version": log.version,
        "tool": log.tool,
        "created_at": log.created_at,
        "root": str(log.root),
        "moves": [
            {
                "from": str(item.source),
                "to": str(item.destination),
                "sha256": item.sha256,
            }
            for item in log.moves
        ],
    }


def write_log(log: UndoLog, path: Path) -> Path:
    """Write ``log`` as pretty-printed JSON and return ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(log_to_dict(log), indent=2) + "\n", encoding="utf-8")
    return path


def load_log(path: Path) -> UndoLog:
    """Read and validate an undo log file."""
    if not path.exists():
        raise UndoError(f"no undo log found at {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise UndoError(f"undo log is not valid JSON: {exc}") from exc
    if not isinstance(data, dict) or data.get("tool") not in (None, "tidyfolder"):
        raise UndoError(f"file is not a tidyfolder undo log: {path}")
    if int(data.get("version", 1)) > LOG_VERSION:
        raise UndoError(
            f"undo log version {data.get('version')} is newer than this "
            f"tidyfolder supports ({LOG_VERSION})"
        )
    moves = []
    for raw in data.get("moves", []):
        moves.append(
            LoggedMove(
                source=Path(raw["from"]),
                destination=Path(raw["to"]),
                sha256=raw.get("sha256"),
            )
        )
    root = Path(data.get("root", path.parent))
    return UndoLog(
        root=root,
        created_at=str(data.get("created_at", "")),
        moves=moves,
        version=int(data.get("version", 1)),
        tool=str(data.get("tool", "tidyfolder")),
    )


def _remove_empty_parents(path: Path, stop: Path) -> None:
    """Remove empty directories from ``path`` up to (but not including) ``stop``."""
    current = path
    while current != stop and stop in current.parents:
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def apply_undo(
    log: UndoLog,
    *,
    dry_run: bool = False,
    force: bool = False,
    log_path: Optional[Path] = None,
) -> UndoResult:
    """Move files back to their original locations.

    If a recorded SHA-256 no longer matches, the file is skipped unless
    ``force`` is True. Existing files at the original path are never
    overwritten; a numeric suffix is added instead.
    """
    result = UndoResult(
        root=log.root,
        log_path=log_path or default_log_path(log.root),
        dry_run=dry_run,
    )

    # Reverse order is safer if any destination later became a source.
    for item in reversed(log.moves):
        if not item.destination.exists():
            result.skipped.append(
                f"missing: {item.destination} (already moved or deleted)"
            )
            continue
        if item.sha256 and item.destination.is_file():
            current = file_sha256(item.destination)
            if current != item.sha256 and not force:
                result.skipped.append(
                    f"hash mismatch: {item.destination} has changed since it "
                    "was organized; pass --force to move it anyway"
                )
                continue
        target = item.source
        if target.exists():
            target = unique_destination(target)
        if dry_run:
            # Record the intended target so the preview is accurate.
            item.source = target
            result.restored.append(item)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(item.destination), str(target))
        _remove_empty_parents(item.destination.parent, log.root)
        item.source = target
        result.restored.append(item)

    if not dry_run and log_path and log_path.exists() and not result.skipped:
        # Keep a copy so a failed partial undo can still be retried;
        # only remove the log when everything was restored.
        log_path.unlink()
    return result
