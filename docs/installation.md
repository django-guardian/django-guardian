---
title: Install
description: Getting started with django-guardian.
---

# Installation

This application requires [Django](http://www.djangoproject.com/) 3.2 or higher.
It is the only prerequisite before `django-guardian` may be used.

```shell
pip install django-guardian
```

`django-guardian` needs to be [configured](./configuration.md) in your django settings.

Additional dependencies are required to run tests or the example application, see [Testing](./develop/testing.md)
and [Example project](./userguide/examples.md).

## Starting a new project

By default, Guardian uses generic foreign keys to retain relation with any Django model which 
has implications on performance. 
If you're starting a new project, you may want to read the following sections of the documentation:

1. [performance tuning docs](./userguide/performance.md) 
2. [Configuration docs](./configuration.md)
