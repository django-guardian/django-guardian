---
title: Testing
description: How to run the test harness, generate coverage reports, and other considerations while writing unit tests.
---

# Testing

The full contributor workflow, branch policy, PR expectations, and AI/LLM policy are documented in the root [`CONTRIBUTING.md`](https://github.com/django-guardian/django-guardian/blob/main/CONTRIBUTING.md).

This page focuses specifically on running the test and verification tooling used by this repository.

`django-guardian` extends Django's authorization framework, so regressions can have security implications. Changes in permission logic should be treated as security-sensitive and verified thoroughly.

!!! danger "Security Risks"
    If you spot a *security risk* or a bug that might affect security of systems that use `django-guardian`,

    **DO NOT create a public issue**.

    Instead, follow the process in the project's [security policy](https://github.com/django-guardian/django-guardian/blob/main/SECURITY.md)
    and use the repository's [private vulnerability reporting flow](https://github.com/django-guardian/django-guardian/security).

If you find a non-security related bug in this project,
please take a minute and file a ticket in our
[issue tracker](https://github.com/django-guardian/django-guardian/issues).

## Local setup

Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) and sync the development environment:

```shell
uv sync --group dev
```

If you need the optional database dependencies used by the broader CI matrix, sync the `ci` dependency group instead:

```shell
uv sync --group ci
```

## Running tests

The fastest local test command is the main `pytest` suite with coverage:

```shell
uv run pytest --cov=guardian --cov-report=xml --cov-report=term
```

Makefile alias:

```shell
make test
```

If you want full matrix parity with the environments defined in `tox.ini`, run:

```shell
uv run tox run
```

To run a specific environment only:

```shell
uv run tox run -e core-py313-django51
uv run tox run -e type-py313
uv run tox run -e docs-py313-django51
```

Makefile alias for the full matrix:

```shell
make test-all
```

## Coverage support

[Coverage](http://nedbatchelder.com/code/coverage/) is a tool for
measuring code coverage of Python programs. It is great for tests and we
use it as a backup - we try to cover 100% of the code used by
`django-guardian`. This of course does *NOT* mean that if all of the
codebase is covered by tests we can be sure there is no bug (as
specification of almost all applications requires some unique scenarios
to be tested). On the other hand it definitely helps to track missing
parts.

The repository's standard coverage command is already included in the default pytest invocation:

```shell
uv run pytest --cov=guardian --cov-report=xml --cov-report=term
```

This produces:

- terminal coverage output for quick review
- `coverage.xml` for CI/reporting integrations

## Tox

`tox` is the canonical way to exercise the supported Python/Django combinations,
type-checking environment, docs build environment, and example project checks.

```shell
uv run tox run
```

Useful examples:

```shell
uv run tox run -e core-py314-django52
uv run tox run -e core-py312-djangomain
uv run tox run -e example-py313-django51
uv run tox run -e examplegroup-py313-django51
```

If you change models or permission schema state, also run the migration sanity check used by the Django tox environments:

```shell
uv run python manage.py makemigrations --check --dry-run
```

## Linting, typing, and docs verification

Repository changes should usually be verified with more than just tests.

```shell
uv run ruff check .
uv run mypy ./guardian
uv run mkdocs build
```

Makefile aliases:

```shell
make lint
make docs
```

## GitHub Actions

We have support for [GitHub Actions](https://github.com/django-guardian/django-guardian/actions)
to run the same general checks in CI. Local verification with `pytest`, `tox`, `ruff`, `mypy`, and `mkdocs` helps catch problems before you open or update a pull request.
