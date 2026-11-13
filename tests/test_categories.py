"""Tests for default category lookup."""

from __future__ import annotations

from tidyfolder.categories import (
    DEFAULT_OTHER_FOLDER,
    build_extension_map,
    category_for,
    default_extension_map,
)


def test_common_extensions_map_to_expected_categories() -> None:
    mapping = default_extension_map()
    assert category_for("photo.JPG", mapping) == "Images"
    assert category_for("clip.mp4", mapping) == "Videos"
    assert category_for("song.mp3", mapping) == "Audio"
    assert category_for("report.pdf", mapping) == "Documents"
    assert category_for("data.xlsx", mapping) == "Spreadsheets"
    assert category_for("slides.pptx", mapping) == "Presentations"
    assert category_for("bundle.zip", mapping) == "Archives"
    assert category_for("app.py", mapping) == "Code"
    assert category_for("setup.msi", mapping) == "Installers"
    assert category_for("Inter.ttf", mapping) == "Fonts"


def test_unknown_and_extensionless_files_go_to_other() -> None:
    mapping = default_extension_map()
    assert category_for("file.unknownext", mapping) == DEFAULT_OTHER_FOLDER
    assert category_for("README", mapping) == DEFAULT_OTHER_FOLDER
    assert category_for(".gitignore", mapping) == DEFAULT_OTHER_FOLDER


def test_compound_extensions_use_the_last_suffix() -> None:
    mapping = default_extension_map()
    assert category_for("backup.tar.gz", mapping) == "Archives"


def test_custom_categories_override_defaults() -> None:
    mapping = build_extension_map({"Design": [".psd", "AI"]})
    assert mapping[".psd"] == "Design"
    assert mapping[".ai"] == "Design"
    assert category_for("logo.psd", mapping) == "Design"
