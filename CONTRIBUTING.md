# Contributing to `django-guardian`

Thank you for contributing to `django-guardian`.

This project sits in the authorization and object-permission layer of Django applications, so correctness, backwards compatibility, and security matter as much as feature delivery. This document is the canonical contributor guide for the repository. Supporting docs under `docs/develop/` may explain individual tools in more detail, but maintainers review contributions against the standards in this file.

## Before you start work

### File an issue first

For bug reports, feature requests, behavioral changes, or larger refactors, start by opening an issue in the repository:

- <https://github.com/django-guardian/django-guardian/issues>

This helps confirm that the proposal fits the project roadmap before significant implementation work begins. PRs that arrive without prior context may be closed if they are out of scope, too risky, or difficult to support long-term.

### Do not report vulnerabilities publicly

If you suspect a security issue, do **not** open a public issue or PR.

Follow the process in `SECURITY.md` and use GitHub's private vulnerability reporting flow instead:

- <https://github.com/django-guardian/django-guardian/security>

## Branching and pull requests

`django-guardian` uses two important long-lived branches:

- `main`: latest stable release branch
- `next`: integration branch for upcoming release candidates and unreleased work

### Which branch should my PR target?

Unless a maintainer explicitly asks otherwise, open pull requests against `next`.

`main` should stay production-ready. New features and normal fixes should land in `next` first and then roll into the next release. If an urgent hotfix is needed for `main`, coordinate with the maintainers before opening the PR.

### Recommended workflow

1. Fork the repository.
2. Clone your fork locally.
3. Create a focused branch from `next`.
4. Make the change with tests and documentation updates where relevant.
5. Run the local checks listed below.
6. Push your branch and open a PR against `next`.

## Development environment

The repository uses `uv` for dependency management and command execution.

### Initial setup

1. Install `uv`:
   - <https://docs.astral.sh/uv/getting-started/installation/>
2. Clone your fork of the repository.
3. Sync the development environment:

```bash
uv sync --group dev
```

This creates and manages a local virtual environment and installs the package together with the development dependencies declared in `pyproject.toml`.

If you want the broader dependency set used by CI for optional database backends, sync the `ci` group instead:

```bash
uv sync --group ci
```

## Local quality checks

Run these before opening or updating a PR.

### Run the main test suite

```bash
uv run pytest --cov=guardian --cov-report=xml --cov-report=term
```

Makefile alias:

```bash
make test
```

### Run the full tox matrix

Use `tox` when you want parity with the supported Python/Django matrix, type-checking envs, docs build envs, and example project checks defined in `tox.ini`.

```bash
uv run tox run
```

To run a single environment:

```bash
uv run tox run -e core-py313-django51
uv run tox run -e type-py313
uv run tox run -e docs-py313-django51
```

Makefile alias for the full matrix:

```bash
make test-all
```

### Lint and type-check

```bash
uv run ruff check .
uv run mypy ./guardian
```

Makefile alias:

```bash
make lint
```

### Auto-format before committing

```bash
uv run ruff check --fix .
uv run ruff format .
```

Makefile alias:

```bash
make format
```

### Build the documentation

```bash
uv run mkdocs build
```

To preview docs locally:

```bash
uv run mkdocs serve
```

Makefile aliases:

```bash
make docs
make docs-serve
```

### Migration sanity check

If your change touches models, permissions models, or generated schema state, make sure migrations are in sync:

```bash
uv run python manage.py makemigrations --check --dry-run
```

The tox test environments perform this check automatically for the Django envs.

## Code and review standards

### Tests are required for behavior changes

If you change behavior, fix a bug, optimize performance-sensitive code, or refactor permission logic, add or update tests that prove the change.

`django-guardian` is security-sensitive and tightly integrated with Django's permission framework. A change that "looks right" is not enough; it must be demonstrated through tests.

### Keep changes focused

- Avoid drive-by refactors unrelated to the issue.
- Preserve public APIs unless the change has been discussed first.
- Call out any compatibility, migration, or performance impact in the PR description.
- Update docs for user-visible behavior changes.

### Follow repository tooling

Current repository standards are defined primarily by:

- `pyproject.toml` for dependencies, `ruff`, `mypy`, and `pytest` configuration
- `tox.ini` for the supported test environments
- `Makefile` for convenience commands

If a doc page disagrees with those files, treat the configuration files as the source of truth.

### Add yourself to project metadata

If you would like to be credited as a contributor, add your name to the end of the `authors` list in `pyproject.toml`, preserving the existing ordering convention.

## Pull request checklist

Before requesting review, make sure your PR:

- targets `next` unless a maintainer asked for `main`
- links the relevant issue or clearly explains the context
- includes tests for code changes
- passes formatting, linting, typing, and relevant test commands locally
- updates documentation when behavior or public APIs changed
- explains any security, performance, or compatibility implications

## Policy on AI and LLM usage in contributions

We recognize that Artificial Intelligence (AI) and Large Language Models (LLMs) like GitHub Copilot, ChatGPT, Claude, and Gemini can accelerate development, assist in debugging, and help draft documentation.

However, to maintain the standards, security, and integrity of `django-guardian`, we strictly prohibit **vibe-coding**: blindly generating and pasting code without understanding how it works.

If you use AI tools to assist in your contribution, you must follow the rules below.

### 1. Absolute developer ownership

You are the sole author and owner of the code you submit. **"The AI generated it" is never a valid excuse** for bugs, security vulnerabilities, licensing problems, or architectural flaws.

By submitting a PR, you are asserting that you understand every line of the change, how it integrates with the codebase, and what edge cases it introduces.

### 2. Zero tolerance for vibe-coding and contribution spam

We expect deliberate, context-aware engineering.

- Do not submit raw, unedited LLM output.
- Do not generate PRs just to increase contribution counts.
- Automated or heavily AI-generated PRs that lack human review, project context, or adherence to this repository's standards may be closed without review.

### 3. Verify every API, query, and compatibility claim

LLMs frequently hallucinate APIs, invent nonexistent libraries, and suggest outdated or deprecated patterns.

You must manually verify that AI-assisted changes do not introduce:

- fake Django or Python APIs
- deprecated Django behavior that will break in supported versions
- incorrect query patterns that create N+1 issues or permission leakage
- inaccurate typing, migration, or configuration changes

### 4. Mandatory testing and verification

AI output is probabilistic, not authoritative. Any AI-assisted logic change, refactor, or optimization must be covered by robust tests and verified locally with the repository tooling.

For non-trivial changes, that typically means running some combination of:

- `uv run pytest --cov=guardian --cov-report=xml --cov-report=term`
- `uv run tox run`
- `uv run ruff check .`
- `uv run mypy ./guardian`

If the change affects docs, examples, or release flow, verify those too.

### 5. Security and intellectual property

LLMs are trained on large volumes of public code and can sometimes reproduce copyrighted snippets or reintroduce known vulnerabilities.

It is your responsibility to ensure that your contribution:

- does not violate project licensing expectations
- follows Django security best practices
- does not expose private data, unsafe serialization, SQL injection risk, or permission bypasses

### 6. Transparency and disclosure

If a significant portion of your implementation, architecture, or refactoring was drafted with AI assistance, disclose that in the PR description.

Example:

> *Note: I used [Tool Name] to help draft the initial logic for this change. I manually reviewed and adapted the result to fit `django-guardian`, and I added tests and local verification for the final implementation.*
