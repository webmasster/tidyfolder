"""End-to-end tests for the tidyfolder command-line interface."""

from __future__ import annotations

from pathlib import Path

import pytest

from tidyfolder.cli import main


def test_organize_dry_run_and_apply(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "photo.jpg").write_bytes(b"img")
    (tmp_path / "notes.pdf").write_bytes(b"pdf")

    assert main(["organize", str(tmp_path), "--dry-run"]) == 0
    captured = capsys.readouterr()
    assert "Would move 2 file(s)." in captured.out
    assert (tmp_path / "photo.jpg").exists()

    assert main(["organize", str(tmp_path)]) == 0
    captured = capsys.readouterr()
    assert "Moved 2 file(s)." in captured.out
    assert "Undo log written" in captured.out
    assert (tmp_path / "Images" / "photo.jpg").is_file()
    assert (tmp_path / ".tidyfolder-undo.json").is_file()


def test_cli_undo_restores_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "photo.jpg").write_bytes(b"img")
    assert main(["organize", str(tmp_path)]) == 0
    capsys.readouterr()
    assert main(["undo", str(tmp_path)]) == 0
    captured = capsys.readouterr()
    assert "Restored 1 file(s)." in captured.out
    assert (tmp_path / "photo.jpg").read_bytes() == b"img"


def test_cli_dupes_and_categories(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "one.bin").write_bytes(b"same")
    (tmp_path / "two.bin").write_bytes(b"same")
    assert main(["dupes", str(tmp_path)]) == 0
    captured = capsys.readouterr()
    assert "duplicate group" in captured.out
    assert "Wasted space" in captured.out

    assert main(["categories", str(tmp_path)]) == 0
    captured = capsys.readouterr()
    assert "Images" in captured.out
    assert ".jpg" in captured.out


def test_cli_refuses_missing_path(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["organize", "/definitely/not/a/real/path/tidyfolder"]) == 2
    captured = capsys.readouterr()
    assert "does not exist" in captured.err


def test_cli_uses_local_config(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "logo.psd").write_bytes(b"psd")
    (tmp_path / "tidyfolder.toml").write_text(
        "[categories.Design]\nextensions = [\".psd\"]\n",
        encoding="utf-8",
    )
    assert main(["organize", str(tmp_path), "--dry-run"]) == 0
    captured = capsys.readouterr()
    assert "Design/logo.psd" in captured.out
    assert "Using config:" in captured.out

