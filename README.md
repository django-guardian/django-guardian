# django-guardian

[![Tests](https://github.com/django-guardian/django-guardian/workflows/Tests/badge.svg?branch=devel)](https://github.com/django-guardian/django-guardian/actions/workflows/tests.yml)
[![PyPI version](https://img.shields.io/pypi/v/django-guardian.svg)](https://pypi.python.org/pypi/django-guardian)
[![Python versions](https://img.shields.io/pypi/pyversions/django-guardian.svg)](https://pypi.python.org/pypi/django-guardian)

`django-guardian` is an implementation of _per-object permissions_ on top
of Django’s authorization backend. Read an introduction to per-object permissions [on djangoadvent articles](https://github.com/djangoadvent/djangoadvent-articles/blob/master/1.2/06_object-permissions.rst).

## Documentation

Online documentation is available at [https://django-guardian.readthedocs.io/](https://django-guardian.readthedocs.io/).

## Requirements

- Python 3.8+
- A supported version of Django (currently 3.2+)

GitHub Actions run tests against Django versions 3.2, 4.1, 4.2, 5.0, 5.1 and main.

## Installation

To install `django-guardian` simply run:

```bash
pip install django-guardian
```

## Configuration

We need to hook `django-guardian`` into our project.

1. Put `guardian` into your `INSTALLED_APPS` at settings module:

```python
    INSTALLED_APPS = (
     ...
     'guardian',
    )
```

2. Add extra authorization backend to your `settings.py`:

```py
    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'guardian.backends.ObjectPermissionBackend',
    )
```

3. Create `guardian` database tables by running::

```
     python manage.py migrate
```

## Usage

After installation and project hooks we can finally use object permissions
with Django.

Lets start really quickly:

```py
      >>> from django.contrib.auth.models import User, Group
      >>> jack = User.objects.create_user('jack', 'jack@example.com', 'topsecretagentjack')
      >>> admins = Group.objects.create(name='admins')
      >>> jack.has_perm('change_group', admins)
      False
      >>> from guardian.shortcuts import assign_perm
      >>> assign_perm('change_group', jack, obj=admins)
      <UserObjectPermission: admins | jack | change_group>
      >>> jack.has_perm('change_group', admins)
      True
```

Of course our agent jack here would not be able to _change_group_ globally:

```py

    >>> jack.has_perm('change_group')
    False
```

## Admin integration

Replace `admin.ModelAdmin` with `GuardedModelAdmin` for those models
which should have object permissions support within admin panel.

For example:

```py
    from django.contrib import admin
    from myapp.models import Author
    from guardian.admin import GuardedModelAdmin

    # Old way:
    #class AuthorAdmin(admin.ModelAdmin):
    #    pass

    # With object permissions support
    class AuthorAdmin(GuardedModelAdmin):
        pass

    admin.site.register(Author, AuthorAdmin)
```
