---
title: Makefile Commands
description: How to use the Makefile commands for building, testing, and development tasks.
---

# Makefile Commands

Django Guardian includes a comprehensive Makefile that provides convenient commands for common development tasks. The Makefile uses `uv` as the package manager and includes commands for building, testing, linting, and more.

## Prerequisites

Before using the Makefile commands, ensure you have:

- `uv` package manager installed
- A virtual environment activated (if using one)
- Development dependencies installed (`uv pip install -e . --group dev`)

## Available Commands

To see all available commands with descriptions:

```shell
$ make help
```

This will display:

```
Available commands:
  build        - Build the package
  pytest       - Run tests with pytest
  test         - Alias for pytest
  clean        - Clean build artifacts
  install      - Install the package
  dev-install  - Install package in development mode with dev dependencies
  lint         - Run linting checks
  format       - Format code
  docs         - Build documentation
```

## Core Commands

### Building the Package

To build the django-guardian package (creates both source distribution and wheel):

```shell
$ make build
```

This command uses `uv build` to create distribution files in the `dist/` directory.

### Running Tests

To run the test suite with pytest and coverage reporting:

```shell
$ make pytest
```

Or use the alias:

```shell
$ make test
```

This command runs pytest with coverage for the guardian module and generates both XML and terminal coverage reports.

## Development Commands

### Installing Dependencies

To install the package in development mode with all development dependencies:

```shell
$ make dev-install
```

For a regular installation:

```shell
$ make install
```

### Code Quality

To run linting checks (ruff and mypy):

```shell
$ make lint
```

To format code using ruff:

```shell
$ make format
```

### Documentation

To build the documentation using mkdocs:

```shell
$ make docs
```

### Cleaning Build Artifacts

To clean up build artifacts, distribution files, and cache:

```shell
$ make clean
```

This removes:
- `build/` directory
- `dist/` directory
- `*.egg-info/` directories
- `__pycache__` directories
- `.pyc` files

## Usage Examples

Here are some common development workflows using the Makefile:

### Setting up for development:

```shell
$ make dev-install
$ make test
```

### Before committing changes:

```shell
$ make format
$ make lint
$ make test
```

### Creating a release:

```shell
$ make clean
$ make build
```

### Full development cycle:

```shell
# Setup
$ make dev-install

# Development
$ make format
$ make lint
$ make test

# Build and documentation
$ make build
$ make docs

# Cleanup
$ make clean
```

## Notes

- All commands use `uv` as the package manager, which is faster and more reliable than pip
- The Makefile is designed to work with the existing project structure and dependencies
- Commands are optimized for the django-guardian project's specific needs
- Coverage reports are generated automatically when running tests
