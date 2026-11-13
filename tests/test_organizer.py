"""Tests for planning and applying organize runs."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tidyfolder.organizer import organize, plan_moves
from tidyfolder.safety import UnsafePathError


def test_plan_moves_groups_files_by_type(messy_folder: Path) -> None:
    result = plan_moves(messy_folder)
    destinations = {
        move.source.name: move.destination.relative_to(messy_folder).as_posix()
        for move in result.moves
    }
    assert destinations["holiday.jpg"] == "Images/holiday.jpg"
    assert destinations["screenshot.png"] == "Images/screenshot.png"
    assert destinations["resume.pdf"] == "Documents/resume.pdf"
    assert destinations["track.mp3"] == "Audio/track.mp3"
    assert destinations["notes.txt"] == "Documents/notes.txt"
    assert destinations["archive.zip"] == "Archives/archive.zip"
    assert destinations["readme"] == "Other/readme"
    assert ".hidden.env" not in destinations
    assert "tidyfolder.toml" not in destinations
    # Dry planning must not move anything.
    assert (messy_folder / "holiday.jpg").exists()


def test_organize_moves_files_and_is_idempotent(messy_folder: Path) -> None:
    result = organize(messy_folder)
    assert result.applied == 7
    assert (messy_folder / "Images" / "holiday.jpg").is_file()
    assert (messy_folder / "Documents" / "resume.pdf").is_file()
    assert not (messy_folder / "holiday.jpg").exists()

    second = organize(messy_folder)
    assert second.moves == []
    assert second.applied == 0
    assert (messy_folder / "Images" / "holiday.jpg").is_file()

    # With --recursive, already-sorted files are counted as skipped, not moved again.
    recursive = organize(messy_folder, recursive=True)
    assert recursive.moves == []
    assert recursive.skipped >= 7


def test_name_collision_gets_numeric_suffix(tmp_path: Path) -> None:
    (tmp_path / "Images").mkdir()
    (tmp_path / "Images" / "photo.jpg").write_bytes(b"already-there")
    (tmp_path / "photo.jpg").write_bytes(b"new-file")
    result = organize(tmp_path)
    assert len(result.moves) == 1
    assert result.moves[0].destination.name == "photo_1.jpg"
    assert (tmp_path / "Images" / "photo.jpg").read_bytes() == b"already-there"
    assert (tmp_path / "Images" / "photo_1.jpg").read_bytes() == b"new-file"


def test_by_date_uses_modification_time(tmp_path: Path) -> None:
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(b"img")
    timestamp = 1_704_067_200  # 2024-01-01 00:00:00 UTC
    os.utime(photo, (timestamp, timestamp))
    result = organize(tmp_path, by_date=True)
    assert result.applied == 1
    dest = result.moves[0].destination
    assert dest.parent.name == "2024-01"
    assert dest.parent.parent.name == "Images"
    assert dest.exists()


def test_exclude_and_recursive(tmp_path: Path) -> None:
    (tmp_path / "keep.jpg").write_bytes(b"a")
    (tmp_path / "skip.jpg").write_bytes(b"b")
    nested = tmp_path / "inbox"
    nested.mkdir()
    (nested / "deep.pdf").write_bytes(b"c")

    top_only = plan_moves(tmp_path)
    names = {move.source.name for move in top_only.moves}
    assert names == {"keep.jpg", "skip.jpg"}

    result = plan_moves(tmp_path, recursive=True, excludes=["skip.*"])
    names = {move.source.name for move in result.moves}
    assert names == {"keep.jpg", "deep.pdf"}


def test_refuses_home_directory_without_force() -> None:
    with pytest.raises(UnsafePathError, match="--force"):
        plan_moves(Path.home())
