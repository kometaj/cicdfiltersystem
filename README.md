# CI/CD Filter System

A command-line utility that evaluates changed repository paths against named glob filters in YAML and writes boolean results to an environment file suitable for CI/CD workflows.

## Features

- YAML configuration with named filters.
- `*` matches characters within one path segment.
- `**` matches zero or more path segments.
- `!pattern` excludes a matching path from that filter.
- `.env` output uses lowercase `true` / `false`.
- Accepts changed paths as command-line arguments or from a newline-delimited file/stdin.
- Automated unit tests and GitHub Actions CI.

## Requirements

- Python 3.12 or newer
- pip

## Install

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
python -m pip install -e ".[dev]"
```

## Configuration

Edit `filters.yaml`:

```yaml
filters:
  backend:
    - "app/src/**/*.kt"
    - "!app/src/test/**"
  frontend:
    - "web/**/*.ts"
    - "web/**/*.tsx"
  docs:
    - "README.md"
    - "docs/**/*.md"
  tests:
    - "**/test/**/*.kt"
```

Each filter must have at least one inclusion pattern. Patterns beginning with `!` are exclusions. A changed file contributes to a filter only when it matches an inclusion and does not match any exclusion for that same filter. A filter is `true` when at least one changed file qualifies.

## Run

Pass paths directly:

```bash
ci-filter --config filters.yaml \
  --files app/src/main/App.kt web/src/app.ts docs/guide.md \
  --output .env
```

Example output:

```text
backend=true
frontend=true
docs=true
tests=false
```

The results are both printed to stdout and written to the requested output file.

For many changed files, use one path per line:

```bash
git diff --name-only origin/main...HEAD > changed-files.txt
ci-filter --config filters.yaml --files-from changed-files.txt --output .env
```

Or pipe paths from stdin:

```bash
git diff --name-only origin/main...HEAD |
  ci-filter --config filters.yaml --files-from - --output .env
```

Run the CLI without installing the console script:

```bash
python -m ci_filter.cli --config filters.yaml --files README.md
```

## Test and lint

```bash
pytest
ruff check .
```

GitHub Actions runs linting and unit tests on pushes and pull requests.

## GitLab CI integration

The utility writes a dotenv-style file, but GitLab CI dotenv reports are primarily intended to pass variables to later jobs; they do not automatically make arbitrary variables usable in `rules` for deciding whether jobs are created. A common approach is to run the filter in a first job, publish `.env` as an artifact, and use a generated child pipeline or another supported pipeline-generation mechanism to conditionally create downstream jobs.

Example filter job:

```yaml
stages: [filter, test]

path_filter:
  stage: filter
  image: python:3.12-slim
  script:
    - pip install .
    - git diff --name-only "$CI_MERGE_REQUEST_DIFF_BASE_SHA" "$CI_COMMIT_SHA" > changed-files.txt
    - ci-filter --config filters.yaml --files-from changed-files.txt --output .env
  artifacts:
    reports:
      dotenv: .env
    paths:
      - .env
```

This demonstrates generating and publishing the results. To use them to decide which jobs exist in the same pipeline, add dynamic child-pipeline generation or use GitLab's native `rules:changes` where appropriate.

## Design notes and trade-offs

- **Glob semantics:** the matcher implements `*`, `**`, `?`, and leading `!` exclusions. It is intentionally not a complete implementation of every shell or Git ignore glob feature (for example, brace expansion and character classes are not implemented).
- **Path scope:** paths are treated as repository-relative POSIX paths. Backslashes and leading `./` are normalized.
- **Exclusion semantics:** exclusions apply to an individual changed file, not the whole filter. A filter can still match if one file is excluded but another included file qualifies.
- **Output safety:** filter names are written as provided, so use simple environment-variable-compatible names (letters, digits, underscores; avoid spaces and punctuation). The tool does not silently rewrite names.
- **Scope:** this version writes the output file directly and does not include signing, release automation, coverage thresholds, or a comprehensive cross-platform test matrix. These are deliberate scope trade-offs for a focused assessment implementation.
- **GitLab behavior:** dotenv variables are available to later jobs but should not be assumed to control `rules` evaluation for jobs already created. Dynamic child pipelines or native `rules:changes` may be needed for true job-selection behavior.

## Error handling

Invalid YAML, missing configuration, malformed filter definitions, and unreadable changed-path files produce an error on stderr and a non-zero exit code.

## Project layout

```text
ci-cd-filter-system/
├── .github/workflows/ci.yml
├── ci_filter/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   └── matcher.py
├── tests/
│   ├── test_cli.py
│   ├── test_config.py
│   └── test_matcher.py
├── filters.yaml
├── pyproject.toml
├── .gitignore
└── README.md
```
