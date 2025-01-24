# Overview

`django-guardian` is an implementation of object permissions for
[Django](http://www.djangoproject.com/) providing an extra
*authentication backend*.

## Features

-   Object permissions for [Django](http://www.djangoproject.com/)
-   AnonymousUser support
-   High level API
-   Heavily tested
-   Django\'s admin integration
-   Decorators

## Incoming

-   Admin templates for
    [grappelli](https://github.com/sehmaschine/django-grappelli)

## Source and issue tracker

Sources are available at
[issue-tracker](http://github.com/lukaszb/django-guardian). You may also
file a bug there.

## Alternate projects

[Django](http://www.djangoproject.com/) still *only* has the foundation
for object permissions[^1] and `django-guardian` makes use of new
facilities and it is based on them. There are some other pluggable
applications which do *NOT* require
[Django](http://www.djangoproject.com/) version 1.2+. For instance,
[django-authority](https://github.com/jazzband/django-authority) or
[django-permissions](https://github.com/lambdalisue/django-permission)
are great options available.

[^1]: See
    <https://docs.djangoproject.com/en/stable/topics/auth/customizing/#handling-object-permissions>
    for more detail.
