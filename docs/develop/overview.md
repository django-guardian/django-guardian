---
title: Contributing
description: Frequently Asked Questions about how to contribute to the django-guardian.
---

# Contributing FAQ

Django Guardian is an open-source project, and we welcome contributions from the community.
However, since Guardian is a security-focused project, there are additional guidelines and rules
for contributors that may be a little different from other open-source projects.

## Why is `next` the default branch?

The `main` branch is always in a production-ready state. The tip of
`main` contains the latest full (ie non-candidate) release. New PRs
should be made into the `next` branch to be first release as a _candidate_
and batched with other PRs into the next versioned release.

The `next` branch, can potentially break. As a user, you should NEVER use
non-main branches in production (if you're desperate
for a feature or fix not yet released, either use a SHA to install at a
specific commit, or install a release candidate tag).

## How do I file a ticket?

Have a bug, feature request, or question?

Create a ticket in [The repo issue tracker](https://github.com/django-guardian/django-guardian/issues)

If you would like to contribute,
it's important to make sure that your ideas are in line with the project goals before you start working.
Describe your bug, feature request, or question with enough details and context to allow the team to understand your request.

## How do I get involved?

You are cordially invited to contribute to the Django Guardian project!
Django Guardian welcomes all types of contributions, from bug reports to documentation.

Start by [filing a ticket](#how-do-i-file-a-ticket) in the issue tracker.

Then, [fork the project on github](https://github.com/django-guardian/django-guardian/fork), create a separate branch, work on it, push changes to your fork and create a pull request.

Here is a quick how to:

1.  Fork a project [here](https://github.com/django-guardian/django-guardian/fork)
2.  Checkout project to your local machine

    ```shell
    $ git clone git@github.com:YOUR_NAME/django-guardian.git
    ```

3.  Create a new branch with name describing change you are going to work on

    ```shell
    $ git checkout -b support-for-custom-model
    ```

4.  Perform changes at newly created branch. Remember to include tests (if this
    is code related change) and run test suite. See `running tests documentation
<testing>`. Also, remember to add yourself to the bottom of the `authors` entry in `pyproject.toml`.

5.  (Optional) Squash commits. If you have multiple commits and it doesn't make
    much sense to have them separated (and it usually makes little sense),
    please consider merging all changes into single commit (if you're not sure about this, the maintainers will likely squash commits on merging, so don't worry too much).

6.  Make sure your PR is up to date with latest changes (it should be ahead of the
    "tip" of the `next` branch that you're mergin into). Please see
    [GitHub's help on interactive rebasing](https://help.github.com/articles/interactive-rebase) if you need help with
    that.

7.  Publish changes

    ```shell
    $ git push origin YOUR_BRANCH_NAME
    ```

8.  Create a [Pull Request](https://help.github.com/articles/creating-a-pull-request).
    Usually it's as simple as opening up https://github.com/YOUR_NAME/django-guardian
    and clicking on review button for newly created branch. There you can make
    final review of your changes and if everything seems fine, create a Pull
    Request.

## Installing dev dependencies and running tests

1. Install the `uv` package manager by [following the instructions here](https://docs.astral.sh/uv/getting-started/installation/).

2. Install tox tool and its plugins into your local environment:
    ```
    uv tool install --python-preference only-managed --python 3.13 tox --with . --with tox-uv
    ```

3. First check all the test environments will install for you (without actually running the tests):
    ```
    tox run -n
    ```

4. Run all the tests:
    ```
    tox run
    ```

Under the hood, the tests use `pytest` so of course, you can set up your IDE to use pytest directly alternatively.


## Why was my issue/pull request closed?

We usually put an explanation when we close an issue or PR. Common reasons:

- no reply for over a month after our last comment or review
- no tests for the changes, or failing tests
- there are performance implications of the changes
- PRs made out of the blue without filing an issue first
- breaking changes we don't want to introduce
- out-of-scope features
- features or approaches that are difficult to support going forwards

## How do I update the documentation?

Documentation is stored in `docs` folder.
To update the documentation, you can edit the Markdown files directly.
If you need to add new pages, or view the documentation locally, you can use the following steps:

1. Install the required packages:

   ```shell
   pip install -r docs/requirements.txt
   ```

2. Run the documentation server:

   ```shell
   mkdocs serve
   ```

The CLI will provide you a link to view the documentation running locally (usually `http://127.0.0.1:8000`).

See the [ReadTheDocs' documentation on using MkDocs](https://docs.readthedocs.com/platform/stable/intro/mkdocs.html)
for more information.

## How do I make a release candidate?

!!! warning
    This workflow may only be triggered by project maintainers.

To make a new _release candidate_ you should perform the following steps:

- Be on any branch other than `main`, typically `next`
- Update `pyproject.toml` with the new version identifier (see [Semantic Versioning 2.0](http://semver.org/)
- Ensure the new identifier ends in `rc<x>`, eg `3.0.0rc1`
- Push your changes to GitHub
- Navigate to [the release-publish action](https://github.com/django-guardian/django-guardian/actions/workflows/release-publish.yml) on GitHub
- Run the workflow manually:
  - Use workflow from branch `devel`.
  - Specify the branch name or commit sha to release
  - Specify the tag to apply, which must match your version identifier (eg `3.0.0rc1`)
- If it is a breaking release, edit release notes to include an "Upgrade Instructions" section

This will:

- build and upload the package to PyPI using a trusted publisher,
- tag the repo, and
- create a prerelease version in GitHub Releases.

## How do I make a full release?

!!! warning
    This workflow may only be triggered by project maintainers.

To make a new full release you should perform the following steps:

- Start on a branch (typically `devel`) where:
  - the tip is at your latest published release candidate and
  - the branch is up to date with `main`
- Update `pyproject.toml` to remove the `rc<x>` suffix from the version identifier
- Commit this change and push to GitHub
- Merge to `main`
- Navigate to [the release-publish action](https://github.com/django-guardian/django-guardian/actions/workflows/release-publish.yml) on GitHub
- Run the workflow manually:
  - Use workflow from branch `main`.
  - Specify the branch name `main`
  - Specify the version identifier eg `3.0.0`
- If it is a breaking release, edit release notes to include an "Upgrade Instructions" section (copy across from the release canditate notes)

This will:

- build and upload the package to PyPI using a trusted publisher,
- tag the repo, and
- create a full release version in GitHub Releases.
