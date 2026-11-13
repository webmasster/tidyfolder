"""Streaming file hashes used by undo logs and duplicate detection."""

from __future__ import annotations

import hashlib
from pathlib import Path

DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1 MiB


def file_sha256(path: Path, chunk_size: int = DEFAULT_CHUNK_SIZE) -> str:
    """Return the hex SHA-256 digest of ``path`` without loading it all at once."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()
