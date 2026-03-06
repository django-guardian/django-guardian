---
title: Object Permissions
description: How to assign object permissions.
---

# Assigning Object Permissions

Django Guardian makes assigning object permissions simple once permissions are created for models.

## Prepare permissions

Take the below example model:

``` python
class Task(models.Model):
    summary = models.CharField(max_length=32)
    content = models.TextField()
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
```

... and we want to be able to set custom permission *assign_task*.
We can let Django know about our custom permissions by adding a `permissions`
tuple to `Meta` class and our final model could look like:

``` python
class Task(models.Model):
    summary = models.CharField(max_length=32)
    content = models.TextField()
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = (
            ('assign_task', 'Assign task'),
        )
```

After we call management commands `makemigrations` and `migrate` our
*assign_task* permission would be added to default set of permissions.

!!! note

    By default, Django adds 4 permissions for each registered model:

    -   *add_modelname*
    -   *change_modelname*
    -   *delete_modelname*
    -   *view_modelname*

    (where *modelname* is a simplified name of our model's class). See
    [https://docs.djangoproject.com/en/stable/topics/auth/default/#default-permissions](https://docs.djangoproject.com/en/stable/topics/auth/default/#default-permissions)
    for more detail.

    There is nothing new here since creation of permissions is [handled by
    django](https://docs.djangoproject.com/en/stable/topics/auth/). Now we
    can move to `assigning object permissions <assign-obj-perms>`

## Using shortcuts

We can assign permissions for any user or group and object pairs
using the convenient function: `guardian.shortcuts.assign_perm()`

### For a single object

Continuing our example we now can allow Joe user to assign some task:

``` python
>>> from django.contrib.auth.models import User
>>> boss = User.objects.create(username='Big Boss')
>>> joe = User.objects.create(username='joe')
>>> task = Task.objects.create(summary='Some job', content='', reported_by=boss)
>>> joe.has_perm('assign_task', task)
False
```

Well, not so fast Joe, let us create an object permission finally:

``` python
>>> from guardian.shortcuts import assign_perm
>>> assign_perm('assign_task', joe, task)
>>> joe.has_perm('assign_task', task)
True
```

This case doesn't really differ for group permissions assignment.
The only difference is we have to pass a `Group` instance rather than `User`.

``` python
>>> from django.contrib.auth.models import Group
>>> group = Group.objects.create(name='employees')
>>> assign_perm('change_task', group, task)
>>> joe.has_perm('change_task', task)
False
>>> # Well, joe is not yet within an *employees* group
>>> joe.groups.add(group)
>>> joe.has_perm('change_task', task)
True
```

### For multiple objects

You can assign a permission to a single user or group across many objects at
once by passing a QuerySet as the `obj` argument:

``` python
>>> tasks = Task.objects.filter(reported_by=boss)
>>> assign_perm('change_task', joe, tasks)
```

### For multiple users or groups

You can assign a permission on a single object to many users or groups at once
by passing a QuerySet as the `user_or_group` argument:

``` python
>>> users = User.objects.filter(groups__name='employees')
>>> assign_perm('change_task', users, task)
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
>>> UserObjectPermission.objects.assign_perm('change_task', joe, task)
```

For a group:

``` python
>>> GroupObjectPermission.objects.assign_perm('change_task', group, task)
```

### For multiple objects

Use `bulk_assign_perm` to assign a permission to one user or group across a
QuerySet of objects:

``` python
>>> tasks = Task.objects.filter(reported_by=boss)
>>> UserObjectPermission.objects.bulk_assign_perm('change_task', joe, tasks)
```

### For multiple users or groups

Use `assign_perm_to_many` to assign a permission on one object to many users or
groups at once:

``` python
>>> users = User.objects.filter(groups__name='employees')
>>> UserObjectPermission.objects.assign_perm_to_many('change_task', users, task)
```

## Limitations

!!! warning

    **No bulk global permissions.** Passing a list or QuerySet of users/groups
    without an object is not supported. Assign global permissions one
    user/group at a time.

!!! warning

    **No dual-bulk operations.** You cannot pass lists for both
    `user_or_group` *and* `obj` at the same time. One side must be a single
    instance. Passing lists for both raises
    `guardian.exceptions.MultipleIdentityAndObjectError`.

!!! note

    **Bulk operations do not fire `post_save` signals.** Bulk assignments use
    `bulk_create()` internally, so per-object `post_save` signals are not
    sent. If you rely on signals, assign permissions individually instead.

## Assigning Permissions inside Signals

Note that the Anonymous User is created before the Permissions are
created. This may result in Django signals, e.g. `post_save` being sent
before the Permissions are created. You will need to take this into an
account when processing the signal.

``` python
@receiver(post_save, sender=User)
def user_post_save(sender, **kwargs):
    """
    Create a Profile instance for all newly created User instances. We only
    run on user creation to avoid having to check for existence on each call
    to User.save.
    """
    user, created = kwargs["instance"], kwargs["created"]
    if created and user.username != settings.ANONYMOUS_USER_NAME:
        from profiles.models import Profile
        profile = Profile.objects.create(pk=user.pk, user=user, creator=user)
        assign_perm("change_user", user, user)
        assign_perm("change_profile", user, profile)
```

The check for `user.username != settings.ANONYMOUS_USER_NAME` is
required otherwise the `assign_perm` calls will occur when the Anonymous
User is created, however before there are any permissions available.
