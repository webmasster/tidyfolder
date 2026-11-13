"""Tests for hash-based duplicate detection."""

from __future__ import annotations

import os
from pathlib import Path

from tidyfolder.duplicates import find_duplicates, plan_duplicate_moves
from tidyfolder.organizer import apply_moves, OrganizeResult


def test_finds_identical_files_and_keeps_the_oldest(tmp_path: Path) -> None:
    older = tmp_path / "original.jpg"
    newer = tmp_path / "copy.jpg"
    unique = tmp_path / "unique.pdf"
    older.write_bytes(b"same-content")
    newer.write_bytes(b"same-content")
    unique.write_bytes(b"other")
    os.utime(older, (1_000_000, 1_000_000))
    os.utime(newer, (2_000_000, 2_000_000))

    result = find_duplicates(tmp_path)
    assert result.scanned == 3
    assert len(result.groups) == 1
    group = result.groups[0]
    assert group.files[0] == older
    assert newer in group.extras
    assert unique not in group.files


def test_plan_and_apply_moves_extras_without_deleting(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_bytes(b"dup")
    (tmp_path / "b.txt").write_bytes(b"dup")
    result = find_duplicates(tmp_path)
    plan_duplicate_moves(result, Path("Duplicates"))
    assert len(result.moves) == 1
    applied = apply_moves(OrganizeResult(root=result.root, moves=result.moves))
    assert applied.applied == 1
    remaining = {path.name for path in tmp_path.iterdir() if path.is_file()}
    extras_dir = tmp_path / "Duplicates"
    assert extras_dir.is_dir()
    assert len(list(extras_dir.iterdir())) == 1
    # One original remains at the top level, plus no data loss.
    assert "a.txt" in remaining or "b.txt" in remaining
    assert {p.read_bytes() for p in extras_dir.iterdir()} == {b"dup"}


def test_no_duplicates_returns_empty_groups(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_bytes(b"one")
    (tmp_path / "b.txt").write_bytes(b"two")
    result = find_duplicates(tmp_path)
    assert result.groups == []
    assert result.scanned == 2
