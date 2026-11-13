"""Tests for TOML configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from tidyfolder.config import ConfigError, discover_config, load_settings, merge_cli


def test_load_settings_merges_categories_and_general(tmp_path: Path) -> None:
    path = tmp_path / "tidyfolder.toml"
    path.write_text(
        "\n".join(
            [
                "[general]",
                "by_date = true",
                'other_folder = "Misc"',
                "",
                "[categories.Design]",
                'extensions = [".psd", "AI"]',
                "",
                "[categories.Images]",
                'extensions = [".jpg"]',
            ]
        ),
        encoding="utf-8",
    )
    settings = load_settings(path)
    assert settings.by_date is True
    assert settings.other_folder == "Misc"
    assert settings.categories["Design"] == (".psd", ".ai")
    assert settings.categories["Images"] == (".jpg",)
    assert "Documents" in settings.categories  # defaults are kept


def test_empty_extensions_removes_a_category(tmp_path: Path) -> None:
    path = tmp_path / "tidyfolder.toml"
    path.write_text("[categories.Fonts]\nextensions = []\n", encoding="utf-8")
    settings = load_settings(path)
    assert "Fonts" not in settings.categories


def test_invalid_toml_raises(tmp_path: Path) -> None:
    path = tmp_path / "tidyfolder.toml"
    path.write_text("this is not = toml [", encoding="utf-8")
    with pytest.raises(ConfigError, match="invalid TOML"):
        load_settings(path)


def test_discover_config_prefers_local_file(tmp_path: Path) -> None:
    local = tmp_path / "tidyfolder.toml"
    local.write_text("[general]\nby_date = true\n", encoding="utf-8")
    found = discover_config(tmp_path)
    assert found == local
    explicit = tmp_path / "custom.toml"
    explicit.write_text("[general]\nby_date = false\n", encoding="utf-8")
    assert discover_config(tmp_path, explicit) == explicit


def test_merge_cli_overrides_config_flags(tmp_path: Path) -> None:
    path = tmp_path / "tidyfolder.toml"
    path.write_text("[general]\nby_date = true\nrecursive = true\n", encoding="utf-8")
    settings = load_settings(path)
    merged = merge_cli(settings, by_date=False, recursive=None)
    assert merged.by_date is False
    assert merged.recursive is True
