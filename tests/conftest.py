"""Shared fixtures for tidyfolder tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def messy_folder(tmp_path: Path) -> Path:
    """Create a typical messy Downloads-style folder."""
    (tmp_path / "holiday.jpg").write_bytes(b"jpeg-bytes")
    (tmp_path / "screenshot.png").write_bytes(b"png-bytes")
    (tmp_path / "resume.pdf").write_bytes(b"pdf-bytes")
    (tmp_path / "track.mp3").write_bytes(b"mp3-bytes")
    (tmp_path / "notes.txt").write_bytes(b"txt-bytes")
    (tmp_path / "archive.zip").write_bytes(b"zip-bytes")
    (tmp_path / "readme").write_bytes(b"no-extension")
    (tmp_path / ".hidden.env").write_text("SECRET=1", encoding="utf-8")
    (tmp_path / "tidyfolder.toml").write_text(
        "[general]\nother_folder = \"Misc\"\n", encoding="utf-8"
    )
    return tmp_path
