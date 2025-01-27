---
title: Testing
description: How to run the test harness, generate coverage reports, and other considerations while writing unit tests.
---

# Testing

## Introduction

According to [OWASP](http://www.owasp.org/),
[broken authentication](http://www.owasp.org/index.php/Top_10_2010-A3) is one of
the most common security issues exposed in web applications.

`django-guardian` extends the capabilities of Django's authorization facilities, 
as such it has to be tested thoroughly.
It is extremely important that Guardian provides the simplest `api` as possible,
with a have a high test scenario coverage.

!!! danger "Security Risks"
    If you spot a *security risk* or a bug that might affect security of systems that use `django-guardian`,

    **DO NOT create a public issue**. 

    Instead, contact the Guardian maintainer team directly.
    You can find contact information in the [SECURITY.md file](https://github.com/django-guardian/django-guardian/blob/devel/.github/SECURITY.md)

If you find a non-security related bug in this application, 
please take a minute and file a ticket in our
[issue-tracker](http://github.com/django-guardian/django-guardian).

## Running tests

Tests are run by Django's building test runner. To call it simply run:

```shell
$ python setup.py test
```

or inside a project with `guardian` set at `INSTALLED_APPS`:

```shell
$ python manage.py test guardian
```

or using the bundled `testapp` project:

```shell
$ python manage.py test
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

To run tests with [coverage](http://nedbatchelder.com/code/coverage/)
support and show the report after we have provided simple bash script
which can by called by running:

```shell
$ ./run_test_and_report.sh
```

Result should be somehow similar to following:

```shell
(...)
................................................
----------------------------------------------------------------------
Ran 48 tests in 2.516s

OK
Destroying test database 'default'...
Name                                  Stmts   Exec  Cover   Missing
-------------------------------------------------------------------
guardian/__init__                         4      4   100%
guardian/backends                        20     20   100%
guardian/conf/__init__                    1      1   100%
guardian/core                            29     29   100%
guardian/exceptions                       8      8   100%
guardian/management/__init__             10     10   100%
guardian/managers                        40     40   100%
guardian/models                          36     36   100%
guardian/shortcuts                       30     30   100%
guardian/templatetags/__init__            1      1   100%
guardian/templatetags/guardian_tags      39     39   100%
guardian/utils                           13     13   100%
-------------------------------------------------------------------
TOTAL                                   231    231   100%
```

## Tox


!!! abstract "Added in version 1.0.4"

We also started using [tox](http://pypi.python.org/pypi/tox) to ensure
`django-guardian`'s tests would pass on all supported Python and Django
versions (see `supported-versions`). 

```shell
pip install tox
```

and run it within `django-guardian` checkout directory:

```shell
tox
```

First time contributors should take some time (it needs to create separate virtual
environments and pull dependencies) but would ensure everything is fine.

## GitHub Actions

!!! abstract "Added in version 2.4.0"

[![image](https://github.com/django-guardian/django-guardian/workflows/Tests/badge.svg?branch=devel)](https://github.com/django-guardian/django-guardian/actions/workflows/tests.yml)

We have support for [GitHub Actions](https://github.com/django-guardian/django-guardian/actions)
to make it easy to follow if test fails with new commits.
