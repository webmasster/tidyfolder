"""Default file-type categories and helpers to look them up."""

from __future__ import annotations

from typing import Dict, Iterable, Mapping, Optional

# Extensions are stored lowercase, including the leading dot.
DEFAULT_CATEGORIES: Dict[str, tuple[str, ...]] = {
    "Images": (
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".bmp",
        ".tif",
        ".tiff",
        ".svg",
        ".heic",
        ".heif",
        ".ico",
        ".raw",
        ".cr2",
        ".nef",
        ".dng",
        ".avif",
    ),
    "Videos": (
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".wmv",
        ".webm",
        ".flv",
        ".m4v",
        ".mpeg",
        ".mpg",
        ".3gp",
    ),
    "Audio": (
        ".mp3",
        ".wav",
        ".flac",
        ".aac",
        ".ogg",
        ".m4a",
        ".wma",
        ".opus",
        ".aiff",
        ".aif",
        ".mid",
        ".midi",
    ),
    "Documents": (
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".rtf",
        ".odt",
        ".md",
        ".markdown",
        ".epub",
        ".pages",
        ".tex",
        ".djvu",
    ),
    "Spreadsheets": (
        ".xls",
        ".xlsx",
        ".csv",
        ".ods",
        ".tsv",
        ".numbers",
    ),
    "Presentations": (
        ".ppt",
        ".pptx",
        ".odp",
        ".key",
    ),
    "Archives": (
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".tgz",
        ".bz2",
        ".xz",
        ".iso",
        ".cab",
    ),
    "Code": (
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".html",
        ".htm",
        ".css",
        ".java",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".cs",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".sh",
        ".bash",
        ".ps1",
        ".json",
        ".xml",
        ".yml",
        ".yaml",
        ".toml",
        ".sql",
        ".ipynb",
        ".kt",
        ".swift",
    ),
    "Installers": (
        ".exe",
        ".msi",
        ".dmg",
        ".pkg",
        ".deb",
        ".rpm",
        ".apk",
        ".appimage",
    ),
    "Fonts": (
        ".ttf",
        ".otf",
        ".woff",
        ".woff2",
        ".eot",
    ),
}

DEFAULT_OTHER_FOLDER = "Other"


def build_extension_map(
    categories: Mapping[str, Iterable[str]],
) -> Dict[str, str]:
    """Return a mapping of lowercase extension -> category name.

    If an extension appears in more than one category, the last one wins.
    """
    mapping: Dict[str, str] = {}
    for category, extensions in categories.items():
        for ext in extensions:
            normalized = ext.lower()
            if not normalized.startswith("."):
                normalized = f".{normalized}"
            mapping[normalized] = category
    return mapping


def category_for(
    filename: str,
    extension_map: Mapping[str, str],
    other_folder: str = DEFAULT_OTHER_FOLDER,
) -> str:
    """Return the category folder name for ``filename``."""
    # Use the last suffix so "archive.tar.gz" can still match ".gz".
    # Files without a suffix go to Other.
    name = filename.lower()
    dot = name.rfind(".")
    if dot <= 0:
        return other_folder
    ext = name[dot:]
    return extension_map.get(ext, other_folder)


def default_extension_map() -> Dict[str, str]:
    """Convenience wrapper around :data:`DEFAULT_CATEGORIES`."""
    return build_extension_map(DEFAULT_CATEGORIES)
