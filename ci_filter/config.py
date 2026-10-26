"""YAML configuration loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when the filter configuration is invalid."""


def load_filters(path: str | Path) -> dict[str, list[str]]:
    """Load and validate the filters mapping from a YAML file."""
    config_path = Path(path)
    try:
        with config_path.open("r", encoding="utf-8") as stream:
            data: Any = yaml.safe_load(stream)
    except OSError as exc:
        raise ConfigError(f"Cannot read config file '{config_path}': {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in '{config_path}': {exc}") from exc

    if not isinstance(data, dict) or not isinstance(data.get("filters"), dict):
        raise ConfigError("Configuration must contain a top-level 'filters' mapping")

    filters: dict[str, list[str]] = {}
    for name, patterns in data["filters"].items():
        if not isinstance(name, str) or not name.strip():
            raise ConfigError("Filter names must be non-empty strings")
        if not isinstance(patterns, list) or not patterns:
            raise ConfigError(f"Filter '{name}' must contain a non-empty list of patterns")
        if any(not isinstance(pattern, str) or not pattern.strip() for pattern in patterns):
            raise ConfigError(f"Filter '{name}' patterns must be non-empty strings")
        if all(pattern.startswith("!") for pattern in patterns):
            raise ConfigError(f"Filter '{name}' must contain at least one inclusion pattern")
        filters[name] = patterns

    return filters
