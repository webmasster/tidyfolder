"""Tests for path safety helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from tidyfolder.safety import (
    UnsafePathError,
    is_dangerous_target,
    is_reserved_name,
    resolve_target,
    should_skip,
    unique_destination,
)


def test_unique_destination_adds_numeric_suffix(tmp_path: Path) -> None:
    existing = tmp_path / "photo.jpg"
    existing.write_bytes(b"one")
    assert unique_destination(existing) == tmp_path / "photo_1.jpg"
    (tmp_path / "photo_1.jpg").write_bytes(b"two")
    assert unique_destination(existing) == tmp_path / "photo_2.jpg"


def test_unique_destination_returns_path_when_free(tmp_path: Path) -> None:
    target = tmp_path / "fresh.txt"
    assert unique_destination(target) == target


def test_reserved_names_are_detected() -> None:
    assert is_reserved_name(Path("/tmp/.tidyfolder-undo.json"))
    assert is_reserved_name(Path("/tmp/tidyfolder.toml"))
    assert not is_reserved_name(Path("/tmp/notes.txt"))


def test_should_skip_hidden_reserved_and_symlinks(tmp_path: Path) -> None:
    hidden = tmp_path / ".secret"
    hidden.write_text("x", encoding="utf-8")
    reserved = tmp_path / ".tidyfolder-undo.json"
    reserved.write_text("{}", encoding="utf-8")
    visible = tmp_path / "ok.txt"
    visible.write_text("ok", encoding="utf-8")
    link = tmp_path / "link.txt"
    link.symlink_to(visible)

    assert should_skip(hidden, tmp_path) is True
    assert should_skip(hidden, tmp_path, include_hidden=True) is False
    assert should_skip(reserved, tmp_path, include_hidden=True) is True
    assert should_skip(visible, tmp_path) is False
    assert should_skip(link, tmp_path) is True
    assert should_skip(visible, tmp_path, extra_excludes=["ok.*"]) is True


def test_resolve_target_rejects_missing_and_files(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    with pytest.raises(UnsafePathError, match="does not exist"):
        resolve_target(missing)
    file_path = tmp_path / "file.txt"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(UnsafePathError, match="not a directory"):
        resolve_target(file_path)
    assert resolve_target(tmp_path) == tmp_path.resolve()


def test_home_and_root_are_dangerous() -> None:
    assert is_dangerous_target(Path.home()) is True
    assert is_dangerous_target(Path("/")) is True
    assert is_dangerous_target(Path("/tmp")) is False
