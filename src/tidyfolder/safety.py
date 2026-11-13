"""Path safety checks and conflict-free destination names."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional


class UnsafePathError(ValueError):
    """Raised when the target path is too broad or otherwise unsafe."""


# Filenames that tidyfolder itself writes and must never move.
RESERVED_NAMES = frozenset(
    {
        ".tidyfolder-undo.json",
        ".tidyfolder-dupes-undo.json",
        "tidyfolder.toml",
        ".tidyfolder.toml",
    }
)

# Directories we refuse to organize unless --force is given.
_FORBIDDEN_NAMES = frozenset(
    {
        "",
        "/",
    }
)


def resolve_target(path: Path) -> Path:
    """Resolve ``path`` and require that it exists and is a directory."""
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise UnsafePathError(f"path does not exist: {path}")
    if not resolved.is_dir():
        raise UnsafePathError(f"path is not a directory: {path}")
    return resolved


def is_dangerous_target(path: Path) -> bool:
    """Return True if organizing this path could be unusually destructive.

    The home directory, filesystem root, and well-known system directories
    should only be touched with an explicit --force flag.
    """
    resolved = path.expanduser().resolve()
    home = Path.home().resolve()
    if resolved == resolved.anchor or str(resolved) in _FORBIDDEN_NAMES:
        return True
    if resolved == home:
        return True
    # Common system roots on Unix and Windows.
    system_roots = [
        Path("/bin"),
        Path("/sbin"),
        Path("/usr"),
        Path("/etc"),
        Path("/dev"),
        Path("/proc"),
        Path("/sys"),
        Path("/boot"),
        Path("/Windows"),
        Path("/System"),
        Path("C:/Windows"),
        Path("C:/Program Files"),
        Path("C:/Program Files (x86)"),
    ]
    for root in system_roots:
        try:
            if resolved == root.resolve() or root.resolve() in resolved.parents:
                return True
        except OSError:
            continue
    return False


def unique_destination(path: Path) -> Path:
    """Return ``path``, or ``stem_N.suffix`` if that name already exists.

    Never overwrites an existing file.
    """
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    n = 1
    while True:
        candidate = parent / f"{stem}_{n}{suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def is_reserved_name(path: Path) -> bool:
    """Return True if this file is an internal tidyfolder artifact."""
    return path.name.lower() in {name.lower() for name in RESERVED_NAMES}


def is_hidden(path: Path, root: Path) -> bool:
    """Return True if the file or any relative parent starts with a dot."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        relative = path
    for part in relative.parts:
        if part.startswith(".") and part not in (".", ".."):
            return True
    return False


def should_skip(
    path: Path,
    root: Path,
    *,
    include_hidden: bool = False,
    extra_excludes: Optional[Iterable[str]] = None,
) -> bool:
    """Return True if ``path`` should be left untouched."""
    if not path.is_file() or path.is_symlink():
        return True
    if is_reserved_name(path):
        return True
    if not include_hidden and is_hidden(path, root):
        return True
    if extra_excludes:
        name = path.name
        rel = str(path.relative_to(root)) if path.is_relative_to(root) else name
        from fnmatch import fnmatch

        for pattern in extra_excludes:
            if fnmatch(name, pattern) or fnmatch(rel, pattern):
                return True
    return False
