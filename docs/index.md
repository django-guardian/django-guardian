---
description: django-guardian documentation. Per-object permissions for Django.
---

# django-guardian - per object permissions for Django

`django-guardian` is an implementation of object permissions for [Django](http://www.djangoproject.com/) providing an extra *authentication backend*.

<div style="display: flex;">
    <div style="flex: 1;">
        <h2>Features</h2>
        <ul>
            <li>Object permissions for <a href="https://www.djangoproject.com/">Django</a></li>
            <li>AnonymousUser support</li>
            <li>High level API</li>
            <li>Heavily tested</li>
            <li>Django's admin integration</li>
            <li>Decorators</li>
        </ul>
    </div>
    <div style="flex: 1; display: flex; justify-content: center; align-items: center;">
        <img alt="A black knights shield" style="max-width: 60%; min-width: 150px; margin-top: 10%;" src="./assets/logo.svg"/>
    </div>
</div>

`django-guardian` supports Python 3.9+ and Django 4.2+.

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
