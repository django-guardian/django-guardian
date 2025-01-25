# django-guardian - per object permissions for Django

[![image](https://github.com/django-guardian/django-guardian/workflows/Tests/badge.svg?branch=devel)](https://github.com/django-guardian/django-guardian/actions/workflows/tests.yml)

`django-guardian` is an implementation of object permissions for [Django](http://www.djangoproject.com/) providing an extra *authentication backend*.

## Features

-   Object permissions for [Django](http://www.djangoproject.com/)
-   AnonymousUser support
-   High level API
-   Heavily tested
-   Django's admin integration
-   Decorators

## Incoming

-   Admin templates for [grappelli](https://github.com/sehmaschine/django-grappelli)

## Source and issue tracker

Sources are available at [issue-tracker](http://github.com/django-guardian/django-guardian). 
You may also file a bug there.

## Alternate projects

[Django](http://www.djangoproject.com/) *only* has the foundation for object-level permissions
<sup> 
    [[1]](#references)
</sup>, 
`django-guardian` makes use of these facilities, and it is based on them. 
There are some other pluggable applications which do *NOT* require [Django](http://www.djangoproject.com/) version 1.2+. 

- [django-authority](https://github.com/jazzband/django-authority)
- [django-permissions](https://github.com/lambdalisue/django-permission)

### References

<sup> 
    [1]
</sup> 
See [https://docs.djangoproject.com/en/stable/topics/auth/customizing/#handling-object-permissions](https://docs.djangoproject.com/en/stable/topics/auth/customizing/#handling-object-permissions) for more detail.
