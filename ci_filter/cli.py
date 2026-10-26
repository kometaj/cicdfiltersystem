"""Command-line interface for ci-filter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ci_filter.config import ConfigError, load_filters
from ci_filter.matcher import evaluate_filters


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ci-filter",
        description="Match changed file paths against YAML-defined CI/CD filters.",
    )
    parser.add_argument("-c", "--config", default="filters.yaml", help="YAML config (default: filters.yaml)")
    parser.add_argument(
        "-f", "--files", nargs="*", default=[],
        help="Changed repository-relative paths (quote paths containing shell metacharacters).",
    )
    parser.add_argument(
        "--files-from", help="Read changed paths from a text file, one path per line; '-' means stdin."
    )
    parser.add_argument("-o", "--output", default=".env", help="Output env file (default: .env)")
    return parser


def _read_paths(args: argparse.Namespace) -> list[str]:
    paths = list(args.files)
    if args.files_from:
        if args.files_from == "-":
            lines = sys.stdin.read().splitlines()
        else:
            try:
                lines = Path(args.files_from).read_text(encoding="utf-8").splitlines()
            except OSError as exc:
                raise ValueError(f"Cannot read changed-path file '{args.files_from}': {exc}") from exc
        paths.extend(line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#"))
    return paths


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        filters = load_filters(args.config)
        changed_paths = _read_paths(args)
        results = evaluate_filters(filters, changed_paths)
        output_path = Path(args.output)
        output_path.write_text(
            "".join(f"{name}={'true' if matched else 'false'}\n" for name, matched in results.items()),
            encoding="utf-8",
        )
    except (ConfigError, ValueError, OSError) as exc:
        print(f"ci-filter: error: {exc}", file=sys.stderr)
        return 2

    for name, matched in results.items():
        print(f"{name}={'true' if matched else 'false'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
