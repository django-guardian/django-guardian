# Overview 

This document contains the FAQs about the development process.

## Why devel is default branch?

Since version 1.2 we try to make `master` in a production-ready state.
It does NOT mean it is production ready, but it SHOULD be. In example,
tests at `master` should always pass. Actually, whole tox suite should
pass. And it's test coverage should be at 100% level.

`devel` branch, on the other hand, can break. It shouldn't but it is
acceptable. As a user, you should NEVER use non-master branches at
production. All the changes are pushed from `devel` to `master` before
next release. It might happen more frequently.

## How to file a ticket/bug/feedback/feature request?

Create a ticket in [The repo issue tracker](https://github.com/django-guardian/django-guardian/issues)

## How do I get involved?

You are cordially invited to contribute to Django Guardian! 

Django Guardian welcomes all types of contributions, from bug reports to, documentation. 
Start by [forking the project on GitHub](https://github.com/django-guardian/django-guardian),
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

We usually put an explanation while we close issue or PR. It might be
for various reasons, i.e., there was no reply for over a month after our
last comment, there were no tests for the changes etc.

## How to do a new release?

To enroll a new release you should perform the following task:

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
To update the documentation, you can edit the markdown files directly. 
If you need to add new pages, or view the documentation locally, you can use the following steps:

Install the required packages:

```shell
pip install -r docs/requirements.txt
```

Run the documentation server:

```shell
mkdocs serve
```

The search functionality may act differently than how they will when deployed to ReadTheDocs.
However, it is enough to get a sense of how the documentation will look.
In addition, the version dropdown and flyout menu will not work 
until the documentation is built and deployed to ReadTheDocs.