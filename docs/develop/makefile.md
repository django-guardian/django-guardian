---
title: Makefile Commands
description: How to use the Makefile commands for building, testing, and development tasks.
---

# Makefile Commands

Django Guardian includes a Makefile that wraps the repository's standard `uv`-based workflow. The targets are convenience aliases for the commands documented in `CONTRIBUTING.md`, `pyproject.toml`, and `tox.ini`.

## Prerequisites

Before using the Makefile commands, ensure you have:

- `uv` package manager installed
- Synced the development environment (`uv sync --group dev`)

Because the Makefile uses `uv run`, you do **not** need to activate a virtual environment manually.

## Available Commands

To see all available commands with descriptions:

```shell
make help
```

This will display:

```
Available commands:
  build        - Build the package
  pytest       - Run tests with pytest
  test         - Alias for pytest
  test-all     - Run the full tox matrix
  clean        - Clean build artifacts
  install      - Sync project dependencies
  dev-install  - Sync project with development dependencies
  lint         - Run linting checks
  format       - Apply Ruff fixes and format code
  docs         - Build documentation
  docs-serve   - Serve documentation locally
  check        - Run lint, tests, and docs build
```

## Core Commands

### Building the Package

To build the django-guardian package (creates both source distribution and wheel):

```shell
make build
```

This command uses `uv build` to create distribution files in the `dist/` directory.

### Running Tests

To run the test suite with pytest and coverage reporting:

```shell
make pytest
```

Or use the alias:

```shell
make test
```

This command runs pytest with coverage for the guardian module and generates both XML and terminal coverage reports.

### Running the Full Matrix

To run the full tox matrix defined in `tox.ini`:

```shell
make test-all
```

This is equivalent to `uv run tox run`.

## Development Commands

### Installing Dependencies

To install the package in development mode with all development dependencies:

```shell
make dev-install
```

This target runs:

```shell
uv sync --group dev
```

For a regular installation:

```shell
make install
```

This target runs:

```shell
uv sync
```

### Code Quality

To run linting checks (ruff and mypy):

```shell
make lint
```

To apply Ruff auto-fixes and then format the code:

```shell
make format
```

### Documentation

To build the documentation using mkdocs:

```shell
make docs
```

To preview the documentation locally:

```shell
make docs-serve
```

To run the most common local verification steps in sequence:

```shell
make check
```

### Cleaning Build Artifacts

To clean up build artifacts, distribution files, and cache:

```shell
make clean
```

This removes:
- `build/` directory
- `dist/` directory
- `*.egg-info/` directories
- `.coverage`
- `.mypy_cache/`
- `.pytest_cache/`
- `.ruff_cache/`
- `.tox/`
- `htmlcov/`
- `__pycache__` directories
- `.pyc` files

## Usage Examples

Here are some common development workflows using the Makefile:

### Setting up for development:

```shell
make dev-install
make test
```

### Before committing changes:

```shell
make format
make lint
make test
```

### Creating a release:

```shell
make clean
make build
```

### Full development cycle:

```shell
# Setup
make dev-install

# Development
make format
make lint
make test

# Build and documentation
make build
make docs

# Cleanup
make clean
```

## Notes

- All executable targets use the repository's managed `uv` environment.
- `Makefile` is a convenience layer; `CONTRIBUTING.md`, `pyproject.toml`, and `tox.ini` remain the canonical sources of truth.
- Coverage reports are generated automatically when running `make pytest` or `make test`.
