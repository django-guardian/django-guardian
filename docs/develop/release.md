---
title: Release Process
description: Step-by-step guide for creating and publishing new releases of django-guardian.
---

# Release Process

!!! warning "Maintainers Only"
    The release workflow can only be triggered by project maintainers with the required permissions.

This document describes the steps to follow when creating a new release of `django-guardian`.
Whether you are creating a standard release, a release candidate (RC), or a hotfix release,
the general process follows the same pattern.

## Prerequisites

Before starting a release, make sure you have:

- Write access to the [django-guardian repository](https://github.com/django-guardian/django-guardian)
- Permission to trigger GitHub Actions workflows
- A local clone of the repository, up to date with the remote
- The development environment synced locally:

    ```shell
    uv sync --group dev
    ```

## Step 1: Run Tests Locally

Before any release, all tests **must** pass. For extra safety, run the test suite locally before
pushing any version bump:

```shell
uv run tox run
```

Or if you want to run a quick check with a single Python/Django combination:

```shell
uv run pytest --cov=guardian --cov-report=xml --cov-report=term
```

!!! tip
    Running tests locally before pushing helps catch issues early, before the CI pipeline runs.
    This is especially important for releases because a failed release workflow can leave things
    in an inconsistent state.

## Step 2: Update the Version in `pyproject.toml`

Open `pyproject.toml` and update the `version` field under `[project]` according to
[Semantic Versioning 2.0](https://semver.org/):

```toml
[project]
version = "X.Y.Z"
```

- **Major** (`X`): Increment for breaking/incompatible changes.
- **Minor** (`Y`): Increment for new features that are backward-compatible.
- **Patch** (`Z`): Increment for backward-compatible bug fixes.
- **Release Candidate**: Append `rc<N>` suffix (e.g. `3.4.0rc1`).

Commit this change:

```shell
git add pyproject.toml
git commit -m "Bump version to X.Y.Z"
git push
```

## Step 3: Trigger the Release Workflow

Navigate to **Actions** → **[Release and Publish](https://github.com/django-guardian/django-guardian/actions/workflows/release-publish.yml)** on GitHub, then click **"Run Workflow"**.

You will be presented with three inputs:

### 3.1 Workflow Branch (Dropdown)

The dropdown at the top ("Use workflow from") determines **which branch the workflow file itself is read from**.
This is _not_ necessarily the branch being released. Select the branch that contains the version of the
workflow you want to use (typically `main`).

!!! note "Workflow branch ≠ Release branch"
    The branch selected in the dropdown controls which version of the workflow YAML is executed.
    The branch/SHA you type into the input field below is the actual code that will be built and released.
    These are two separate concepts.

### 3.2 Branch or Commit SHA to Release

Type the **branch name** or **commit SHA** of the code you want to release:

| Scenario               | Value to enter                                      |
|------------------------|-----------------------------------------------------|
| Standard release       | `main`                                              |
| Release candidate (RC) | The feature/RC branch name (e.g. `next`, `rc/3.4`)  |
| Hotfix release         | The hotfix branch name or a specific commit SHA      |

### 3.3 Tag

Enter the version tag that matches the version you set in `pyproject.toml` (e.g. `3.4.0` or `3.4.0rc1`).

## Step 4: Verify the Release

After the workflow completes, verify that:

1. The package was published to [PyPI](https://pypi.org/project/django-guardian/)
2. A new tag was created in the repository
3. A new release entry was created in [GitHub Releases](https://github.com/django-guardian/django-guardian/releases)

If it is a **breaking release**, edit the release notes on GitHub to include an **"Upgrade Instructions"** section.

---

## Release Types

### Standard (Full) Release

A standard release ships stable, production-ready code from the `main` branch.

1. Ensure `main` is up to date and all tests pass.
2. Update `pyproject.toml` → `version` (remove any `rc` suffix if upgrading from a release candidate).
3. Commit and push to `main`.
4. Trigger the workflow:
    - **Workflow branch (dropdown):** `main`
    - **Branch to release:** `main`
    - **Tag:** the version number (e.g. `3.4.0`)

### Release Candidate (RC)

A release candidate allows testing a new version before making it generally available.

1. Create or use an existing branch (e.g. `next` or `rc/3.4`).
2. Update `pyproject.toml` → `version` with an `rc` suffix (e.g. `3.4.0rc1`).
3. Commit and push to the RC branch.
4. Trigger the workflow:
    - **Workflow branch (dropdown):** the branch containing the workflow file you want to use
    - **Branch to release:** the RC branch name (e.g. `next`)
    - **Tag:** the RC version (e.g. `3.4.0rc1`)

!!! info
    RC releases are marked as **pre-release** in GitHub Releases and are published to PyPI as
    pre-release versions (pip will not install them by default unless `--pre` is specified).

### Hotfix Release

For urgent fixes that need to go out outside the normal release cycle:

1. Create a hotfix branch from the tag of the current release.
2. Apply the fix and update `pyproject.toml` → `version` (increment the patch version).
3. Run tests locally and push.
4. Trigger the workflow with the hotfix branch name or commit SHA.
5. After a successful release, merge the hotfix back into `main` and `next`.

---

## What the Workflow Does

When triggered, the **Release and Publish** workflow will:

1. **Run the full test suite** against the specified branch/commit.
2. **Build** the Python package (sdist and wheel).
3. **Upload** the package to [PyPI](https://pypi.org/project/django-guardian/) using a trusted publisher.
4. **Tag** the repository with the specified version tag.
5. **Create a GitHub Release** (full release or pre-release depending on the tag format).

## Troubleshooting

| Problem                            | Solution                                                                                       |
|------------------------------------|------------------------------------------------------------------------------------------------|
| Workflow fails on tests            | Fix the failing tests, push again, and re-trigger the workflow.                                |
| Version tag already exists         | Delete the existing tag (`git tag -d <tag> && git push origin :refs/tags/<tag>`) and re-run.   |
| Package not appearing on PyPI      | Check the workflow logs for upload errors. Ensure the trusted publisher is configured on PyPI.  |
| Wrong code was released            | Yank the release on PyPI, delete the tag, fix the issue, and re-release with a new patch bump. |
