---
title: Asynchronous views
description: Using PermissionRequiredMixin with asynchronous class-based views.
---

# Asynchronous views

`guardian.mixins.PermissionRequiredMixin` works with asynchronous
class-based views. Django detects a view as asynchronous when all of its
HTTP handlers (`get()`, `post()`, ...) are coroutines. When that is the
case, the mixin runs its permission check asynchronously instead of the
synchronous one.

!!! note
    Asynchronous class-based views require Django >= 4.2.

Synchronous views are unaffected: they keep using `check_permissions()`
and `get_permission_object()` exactly as before, with no additional
overhead.

## Basic usage

Nothing special is required. Declare the handlers as coroutines and the
mixin does the rest:

```python
from django.http import HttpResponse
from django.views.generic import View

from guardian.mixins import PermissionRequiredMixin


class PostView(PermissionRequiredMixin, View):
    permission_required = 'testapp.change_post'
    raise_exception = True

    async def get(self, request, *args, **kwargs):
        return HttpResponse('some html')
```

By default, the object to check the permission against is resolved by
`aget_permission_object()`, which runs the synchronous
`get_permission_object()` in a thread. That is, `permission_object`,
`get_object()` and `object` are honoured as usual.

## Fetching the object with the asynchronous ORM

To avoid the thread hop and use the asynchronous ORM API, override
`aget_permission_object()`:

```python
class PostView(PermissionRequiredMixin, View):
    permission_required = 'testapp.change_post'
    raise_exception = True

    async def aget_permission_object(self):
        return await Post.objects.aget(slug=self.kwargs['slug'])

    async def get(self, request, *args, **kwargs):
        return HttpResponse('some html')
```

An `async def get_object()` or an `async def get_permission_object()` on the
view is awaited as well, so this works too:

```python
class PostView(PermissionRequiredMixin, View):
    permission_required = 'testapp.change_post'

    async def get_object(self):
        return await Post.objects.aget(slug=self.kwargs['slug'])

    async def get(self, request, *args, **kwargs):
        return HttpResponse('some html')
```

## Asynchronous counterparts

Each synchronous method has an `a`-prefixed sister method, following the
naming convention used by Django itself (`aget()`, `acreate()`, ...):

| Synchronous               | Asynchronous               |
|---------------------------|----------------------------|
| `get_permission_object()` | `aget_permission_object()` |
| `check_permissions()`     | `acheck_permissions()`     |
| `dispatch()`              | `adispatch()`              |

`get_required_permissions()`, `get_object_permission_denied_message()` and
`on_permission_check_fail()` have no asynchronous counterpart: they are all
called from a single worker thread, so they may run queries.

If you override `check_permissions()`, override `acheck_permissions()` as
well; asynchronous views do not call the synchronous one.

## Limitations

- Django's generic views other than `View` (`DetailView`, `ListView`, ...)
  define synchronous handlers, so they are never asynchronous views. The
  mixin then uses its synchronous path, as before.
- `LoginRequiredMixin` and `PermissionListMixin` have no asynchronous
  support yet.
- On Django 4.1 and older the synchronous path is used even for
  asynchronous views. Responses for a disallowed HTTP method only became
  awaitable in Django 4.1.2, and 4.1 is end of life, so the floor is 4.2.
