"""Glob matching and filter evaluation."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from pathlib import PurePosixPath


def normalize_path(path: str) -> str:
    """Normalize paths to repository-relative POSIX form."""
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return str(PurePosixPath(normalized))


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Translate a small, documented glob dialect into a full-match regex.

    *  matches any characters except '/' within one path segment.
    ** matches zero or more path segments when followed by '/', or any
       characters including '/' otherwise.
    """
    pattern = pattern.replace("\\", "/")
    out: list[str] = ["^"]
    i = 0

    while i < len(pattern):
        char = pattern[i]
        if char == "*":
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                i += 2
                if i < len(pattern) and pattern[i] == "/":
                    # Zero or more complete path segments, including the slash.
                    out.append("(?:.*/)?")
                    i += 1
                else:
                    out.append(".*")
            else:
                out.append("[^/]*")
                i += 1
        elif char == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(char))
            i += 1

    out.append("$")
    return re.compile("".join(out))


def path_matches(path: str, pattern: str) -> bool:
    """Return whether a repository-relative path matches a glob pattern."""
    return bool(_glob_to_regex(pattern).match(normalize_path(path)))


def evaluate_filters(
    filters: Mapping[str, Sequence[str]], changed_paths: Iterable[str]
) -> dict[str, bool]:
    """Evaluate named filters against changed paths.

    For each filter, at least one inclusion pattern must match a file, and no
    exclusion pattern may match that same file. Exclusions apply per file,
    rather than vetoing an entire filter when another file matches.
    """
    paths = [normalize_path(path) for path in changed_paths]
    results: dict[str, bool] = {}

    for name, patterns in filters.items():
        includes = [p for p in patterns if not p.startswith("!")]
        excludes = [p[1:] for p in patterns if p.startswith("!")]

        if not includes:
            raise ValueError(f"Filter '{name}' must define at least one inclusion pattern")

        results[name] = any(
            any(path_matches(path, pattern) for pattern in includes)
            and not any(path_matches(path, pattern) for pattern in excludes)
            for path in paths
        )

    return results
