---
title: Removing Object Permissions
description: Removing object permissions from users and objects with django-guardian.
---

# Removing Object Permissions

Removing object permissions works just like assigning them. The
`guardian.shortcuts.remove_perm` function accepts the same arguments as
`guardian.shortcuts.assign_perm`, including support for bulk operations on
multiple objects or multiple users/groups.

## Using shortcuts

### For a single object

Assuming Joe has been granted the `change_task` permission on a task:

``` python
>>> from guardian.shortcuts import remove_perm
>>> joe.has_perm('change_task', task)
True
>>> remove_perm('change_task', joe, task)
>>> joe = User.objects.get(username='joe')
>>> joe.has_perm('change_task', task)
False
```

Removing a group permission works the same way — pass a `Group` instance
instead of a `User`:

``` python
>>> from django.contrib.auth.models import Group
>>> group = Group.objects.get(name='employees')
>>> remove_perm('change_task', group, task)
```

### For multiple objects

You can remove a permission from a single user or group across many objects
at once by passing a QuerySet or list as the `obj` argument:

``` python
>>> from guardian.shortcuts import remove_perm
>>> tasks = Task.objects.filter(reported_by=boss)
>>> remove_perm('change_task', joe, tasks)
```

A plain list of objects works too:

``` python
>>> task_list = [task1, task2, task3]
>>> remove_perm('change_task', joe, task_list)
```

The same applies to groups:

``` python
>>> remove_perm('change_task', group, tasks)
```

### For multiple users or groups

You can also remove a permission on a single object from many users or groups
at once by passing a QuerySet or list as the `user_or_group` argument:

``` python
>>> users = User.objects.filter(groups__name='employees')
>>> remove_perm('change_task', users, task)
```

A plain list works as well:

``` python
>>> user_list = [joe, jane]
>>> remove_perm('change_task', user_list, task)
```

And for groups:

``` python
>>> groups = Group.objects.filter(name__startswith='company')
>>> remove_perm('change_task', groups, task)
```

## Using model managers

For more direct control you can call methods on the object-permission model
manager instead of going through the shortcut. First, obtain the permission
model for your object:

``` python
>>> from guardian.utils import get_user_obj_perms_model, get_group_obj_perms_model
>>> UserObjectPermission = get_user_obj_perms_model(task)
>>> GroupObjectPermission = get_group_obj_perms_model(task)
```

### For a single object

``` python
>>> UserObjectPermission.objects.remove_perm('change_task', joe, task)
```

For a group:

``` python
>>> GroupObjectPermission.objects.remove_perm('change_task', group, task)
```

### For multiple objects

Use `bulk_remove_perm` to remove a permission from one user or group across a
QuerySet of objects:

``` python
>>> tasks = Task.objects.filter(reported_by=boss)
>>> UserObjectPermission.objects.bulk_remove_perm('change_task', joe, tasks)
```

### For multiple users or groups

Use `remove_perm_from_many` to remove a permission on one object from many
users or groups at once:

``` python
>>> users = User.objects.filter(groups__name='employees')
>>> UserObjectPermission.objects.remove_perm_from_many('change_task', users, task)
```

## Limitations

!!! warning

    **No bulk global permission removal.** Passing a list or QuerySet of
    users/groups without an object raises
    `guardian.exceptions.MultipleIdentityAndObjectError`. Remove global
    permissions one user/group at a time.

!!! warning

    **No dual-bulk operations.** You cannot pass lists for both
    `user_or_group` *and* `obj` at the same time. One side must be a single
    instance. Passing lists for both raises
    `guardian.exceptions.MultipleIdentityAndObjectError`.

!!! note

    **Bulk operations do not fire `post_delete` signals.** Bulk removals use
    `QuerySet.delete()` internally, so per-object `post_delete` signals are
    not sent. If you rely on signals, remove permissions individually instead.
