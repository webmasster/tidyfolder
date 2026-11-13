"""Load tidyfolder settings from a TOML file."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from tidyfolder.categories import DEFAULT_CATEGORIES, DEFAULT_OTHER_FOLDER

if sys.version_info >= (3, 11):
    import tomllib
else:  # Python 3.10
    import tomli as tomllib


class ConfigError(ValueError):
    """Raised when a config file is missing or invalid."""


@dataclass
class Settings:
    """Effective settings after config and CLI flags are combined."""

    by_date: bool = False
    include_hidden: bool = False
    recursive: bool = False
    other_folder: str = DEFAULT_OTHER_FOLDER
    categories: Dict[str, Tuple[str, ...]] = field(
        default_factory=lambda: {k: tuple(v) for k, v in DEFAULT_CATEGORIES.items()}
    )
    config_path: Optional[Path] = None


def discover_config(root: Path, explicit: Optional[Path] = None) -> Optional[Path]:
    """Return the first existing config path, or None to use built-in defaults.

    Search order: ``--config`` path, ``<root>/tidyfolder.toml``,
    ``<root>/.tidyfolder.toml``, then ``~/.config/tidyfolder/config.toml``.
    """
    if explicit is not None:
        path = explicit.expanduser()
        if not path.is_file():
            raise ConfigError(f"config file not found: {explicit}")
        return path
    candidates = (
        root / "tidyfolder.toml",
        root / ".tidyfolder.toml",
        Path.home() / ".config" / "tidyfolder" / "config.toml",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _as_bool(value: Any, key: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ConfigError(f"{key} must be a boolean, got {value!r}")


def _as_str(value: Any, key: str) -> str:
    if isinstance(value, str) and value.strip():
        return value
    raise ConfigError(f"{key} must be a non-empty string, got {value!r}")


def _as_extensions(value: Any, key: str) -> Tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ConfigError(f"{key} must be a list of strings")
    normalized = []
    for item in value:
        ext = item.lower() if item.startswith(".") else f".{item.lower()}"
        normalized.append(ext)
    return tuple(normalized)


def load_settings(path: Path) -> Settings:
    """Parse a TOML config file into :class:`Settings`."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"cannot read config: {exc}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"config must be a table: {path}")

    settings = Settings(config_path=path)
    general = data.get("general", {})
    if general is None:
        general = {}
    if not isinstance(general, dict):
        raise ConfigError("[general] must be a table")

    if "by_date" in general:
        settings.by_date = _as_bool(general["by_date"], "general.by_date")
    if "include_hidden" in general:
        settings.include_hidden = _as_bool(general["include_hidden"], "general.include_hidden")
    if "recursive" in general:
        settings.recursive = _as_bool(general["recursive"], "general.recursive")
    if "other_folder" in general:
        settings.other_folder = _as_str(general["other_folder"], "general.other_folder")

    categories = data.get("categories")
    if categories is not None:
        if not isinstance(categories, dict):
            raise ConfigError("[categories] must be a table")
        merged = dict(settings.categories)
        for name, body in categories.items():
            if not isinstance(body, dict):
                raise ConfigError(f"[categories.{name}] must be a table")
            if "extensions" not in body:
                raise ConfigError(f"[categories.{name}] needs an extensions list")
            exts = _as_extensions(body["extensions"], f"categories.{name}.extensions")
            if exts:
                merged[name] = exts
            else:
                merged.pop(name, None)
        settings.categories = merged
    return settings


def merge_cli(
    settings: Settings,
    *,
    by_date: Optional[bool] = None,
    include_hidden: Optional[bool] = None,
    recursive: Optional[bool] = None,
) -> Settings:
    """Return a copy of ``settings`` with any explicit CLI flags applied."""
    updates: Dict[str, Any] = {}
    if by_date is not None:
        updates["by_date"] = by_date
    if include_hidden is not None:
        updates["include_hidden"] = include_hidden
    if recursive is not None:
        updates["recursive"] = recursive
    return replace(settings, **updates) if updates else settings


def default_settings() -> Settings:
    """Return built-in defaults with no config file attached."""
    return Settings()
