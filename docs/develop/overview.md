---
title: Contributing
description: Frequently Asked Questions about how to contribute to the django-guardian.
---

# Contributing FAQ

Django Guardian is an open-source project, and we welcome contributions from the community.
However, since Guardian is a security-focused project, there are additional guidelines and rules 
for contributors that may be a little different from other open-source projects.

## Why is `devel` the default branch?

Since version 1.2 we make sure that trunk (i.e., `main`, `master`) is always in a production-ready state.
This means that:
1. The Guardian team tries to keep trunk in a state that it can be released.
2. trunk test coverage is always at 100% (the whole tox suite should pass).

We do not advise that you use trunk in production; production environments should always use a stable release.

On the other hand, it is acceptable for the `devel` branch to *"break"*. 
Client packages and teams should NEVER use non-stable release in production.

## How to file a ticket?

Have a bug, feature request, or question?

Create a ticket in [The repo issue tracker](https://github.com/django-guardian/django-guardian/issues)

If you would like to contribute, 
it's important to make sure that your ideas are in line with the project goals before you start working.
Describe your bug, feature request, or question with enough details and context to allow the team to understand your request.

## How do I get involved?

You are cordially invited to contribute to the Django Guardian project!
Django Guardian welcomes all types of contributions, from bug reports to, documentation. 

Start by [filing a ticket](#how-to-file-a-ticket) in the issue tracker.
After that, [fork the project on GitHub](https://github.com/django-guardian/django-guardian),
create a separate branch, hack on it, publish changes at your fork and create a pull request.

Here is the process in steps:

1.  [Fork a project](https://github.com/django-guardian/django-guardian/fork).

2.  Checkout project to your local machine:

    ```shell
    $ git clone git@github.com:YOUR_NAME/django-guardian.git
    ```

3.  Create a new branch with name describing change you are going to
    work on:

    ```shell
    $ git checkout -b bugfix/support-for-custom-model
    ```
4.  Perform changes at newly created branch. Remember to include tests
    (if this is code related change) and run test suite. See
    `running tests documentation <testing>`. Also, remember to add
    yourself to the `AUTHORS` file.

5.  (Optional) Squash commits. If you have multiple commits, and it makes little sense 
    to have them separated (and it usually makes little sense), 
    please consider merging all changes into single commit. 
    Please see [Git's documentation on interactive rebase](https://help.github.com/articles/interactive-rebase)

6.  Publish changes:

    ```shell
    $ git push origin YOUR_BRANCH_NAME
    ```

7.  [Create a Pull Request](https://help.github.com/articles/creating-a-pull-request).

## Why was my issue/pull request closed?

We usually put an explanation while we close issue or PR. 
It might be for various reasons 
(e.g., there was no reply for an extended period of time after the last comment,
or the issue is a duplicate).

## How to create a new release?

To create a new release, you should perform the following task:

-   Ensure file `CHANGES` reflects all important changes.
-   Ensure file `CHANGES` includes a new version identifier and current release date.
-   Execute `bumpversion patch` (or accordingly - see [Semantic Versioning 2.0](http://semver.org/))
    to reflect changes in codebase.
-   Commit changes of codebase, e.g. `git commit -m "Release 1.4.8" -a`.
-   Tag a new release, e.g. `git tag "v1.4.8"`.
-   Push new tag to repo - `git push origin --tags`.
-   Build a new release - `python3 setup.py sdist bdist_wheel`
-   Push a new release to PyPI - `twine upload`.

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