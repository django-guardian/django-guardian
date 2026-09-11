---
title: Examples
description: Examples on how to use django-guardian to manage object permissions.
---

# Example Projects

Example project should be bundled with archive and be available at
`example_project`. Before you can run it, some requirements have to be
met. Those are easily installed using following command at example
project's directory:

```shell
$ cd example_project
$ pip install -r requirements.txt
```

`django-guardian` from a directory above the `example_project` is
automatically added to Python path at runtime.

And the last thing before we can run example project is to create sqlite database:

```shell
$ ./manage.py migrate
```

Finally we can run dev server:

```shell
$ ./manage.py runserver
```

You should also create a user who can login to the admin site:

```shell
$ ./manage.py createsuperuser
```

Project is really basic and shows almost nothing but eventually it
should expose some `django-guardian` functionality.

To try out
[django-grappelli](https://django-grappelli.readthedocs.io/en/latest/)
integration, set the `GRAPPELLI` environment variable before launching `runserver`.
