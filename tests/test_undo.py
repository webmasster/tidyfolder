"""Tests for the JSON undo log."""

from __future__ import annotations

from pathlib import Path

from tidyfolder.organizer import organize
from tidyfolder.undo import apply_undo, build_log, default_log_path, load_log, write_log


def test_undo_restores_files_and_removes_empty_folders(tmp_path: Path) -> None:
    (tmp_path / "photo.jpg").write_bytes(b"img-data")
    (tmp_path / "notes.pdf").write_bytes(b"pdf-data")
    result = organize(tmp_path)
    log_path = write_log(build_log(result.root, result.moves), default_log_path(result.root))
    assert log_path.is_file()

    loaded = load_log(log_path)
    assert len(loaded.moves) == 2
    undo = apply_undo(loaded, log_path=log_path)
    assert len(undo.restored) == 2
    assert (tmp_path / "photo.jpg").read_bytes() == b"img-data"
    assert (tmp_path / "notes.pdf").read_bytes() == b"pdf-data"
    assert not (tmp_path / "Images").exists()
    assert not (tmp_path / "Documents").exists()
    assert not log_path.exists()


def test_undo_dry_run_does_not_change_files(tmp_path: Path) -> None:
    (tmp_path / "photo.jpg").write_bytes(b"img-data")
    result = organize(tmp_path)
    log_path = write_log(build_log(result.root, result.moves), default_log_path(result.root))
    undo = apply_undo(load_log(log_path), dry_run=True, log_path=log_path)
    assert len(undo.restored) == 1
    assert (tmp_path / "Images" / "photo.jpg").exists()
    assert log_path.exists()


def test_hash_mismatch_is_skipped_unless_forced(tmp_path: Path) -> None:
    original = tmp_path / "photo.jpg"
    original.write_bytes(b"original")
    result = organize(tmp_path)
    log_path = write_log(build_log(result.root, result.moves), default_log_path(result.root))
    moved = tmp_path / "Images" / "photo.jpg"
    moved.write_bytes(b"changed-after-organize")

    skipped = apply_undo(load_log(log_path), log_path=log_path)
    assert skipped.restored == []
    assert len(skipped.skipped) == 1
    assert "hash mismatch" in skipped.skipped[0]
    assert moved.exists()

    forced = apply_undo(load_log(log_path), force=True, log_path=log_path)
    assert len(forced.restored) == 1
    assert (tmp_path / "photo.jpg").read_bytes() == b"changed-after-organize"
