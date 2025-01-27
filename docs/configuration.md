---
title: Configuration
description: Configuration options and django settings for django-guardian.
---

# Configuration

After [installation](./installation.md), we can prepare our project for object permissions handling.
In a settings module we need to add guardian to `INSTALLED_APPS`:

```python
INSTALLED_APPS = (
    # ...
    'guardian',
)
```

and hook guardian's authentication backend:

```python
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # this is default
    'guardian.backends.ObjectPermissionBackend',
)
```

!!! note

    Once project is configured to work with `django-guardian`, calling
    `migrate` management command would create `User` instance for anonymous
    user support (with name of `AnonymousUser`).

!!! note

    The Guardian anonymous user is different from the Django Anonymous user.
    The Django Anonymous user does not have an entry in the database,
    however the Guardian anonymous user does. This means that the following
    code will return an unexpected result:

    ``` python
    from django.contrib.auth import get_user_model
    User = get_user_model()
    anon = User.get_anonymous()
    anon.is_anonymous  # returns False
    ```


We can change id to whatever we like. Project should be now ready to use
object permissions.

# Optional settings

Guardian has the following, optional configuration variables:

## `GUARDIAN_RAISE_403`

!!! abstract "Added in version 1.0.4"

If set to `True`, guardian would raise `django.core.exceptions.PermissionDenied` error instead of returning 
empty `django.http.HttpResponseForbidden`.

!!! warning

    Remember that you cannot use both
    `GUARDIAN_RENDER_403` **AND** `GUARDIAN_RAISE_403` - if both are set
    to `True`, `django.core.exceptions.ImproperlyConfigured` would be raised.

## `GUARDIAN_RENDER_403`

!!! abstract "Added in version 1.0.4"

If set to `True`, guardian would try to render 403 response rather than
return content less `django.http.HttpResponseForbidden`. 
Would use template pointed by `GUARDIAN_TEMPLATE_403` to do that. Default is `False`.

!!! warning

    Remember that you cannot use both
    `GUARDIAN_RENDER_403`{.interpreted-text role="setting"} **AND**
    `GUARDIAN_RAISE_403`{.interpreted-text role="setting"} - if both are set
    to `True`, `django.core.exceptions.ImproperlyConfigured` would be
    raised.

## `GUARDIAN_TEMPLATE_403`

!!! abstract "Added in version 1.0.4"

Tells parts of guardian what template to use for responses with status
code `403` (i.e. `api-decorators-permission_required`). Defaults to `403.html`.


## `ANONYMOUS_USER_NAME`

!!! abstract "Added in version 1.4.2"

This is the username of the anonymous user. Used to create the anonymous
user and subsequently fetch the anonymous user as required.

If `ANONYMOUS_USER_NAME` is set to `None`, anonymous user object
permissions-are disabled. You may need to choose this option if creating
an `User` object-to represent anonymous users would be problematic in
your environment.

Defaults to `"AnonymousUser"`.


!!! tip 
    [Django's docs on substituting a custom user model](https://docs.djangoproject.com/en/stable/topics/auth/customizing/#substituting-a-custom-user-model)

## `GUARDIAN_GET_INIT_ANONYMOUS_USER`

!!! abstract "Added in version 1.2"

Guardian supports object level permissions for anonymous users, however,
when in our project we use a custom User model, default function might
fail. This can lead to issues as `guardian` tries to create anonymous
user after each `migrate` call. Object that is going to be created is
retrieved using function pointed by this setting. Once retrieved, `save`
method would be called on that instance.

Defaults to `"guardian.management.get_init_anonymous_user"`.

!!! tip "See also `custom-user-model-anonymous`"

## `GUARDIAN_GET_CONTENT_TYPE`

!!! info "Added in 1.5"

Guardian allows applications to supply a custom function to retrieve the
content type from objects and models. This is useful when a class or
class hierarchy uses the `ContentType` framework in an non-standard way.
Most applications will not have to change this setting.

As an example, when using `django-polymorphic` it\'s useful to use a
permission on the base model which applies to all child models. In this
case, the custom function would return the `ContentType` of the base
class for polymorphic models and the regular model `ContentType` for
non-polymorphic classes.

Defaults to `"guardian.ctypes.get_default_content_type"`.

## `GUARDIAN_AUTO_PREFETCH`

!!! abstract "Added in version 2.0.0"

For vanilla deployments using standard `ContentType` interfaces and
default `UserObjectPermission` or `GroupObjectPermission` models,
Guardian can automatically prefetch all User permissions for all object
types. This can be useful when manual prefetching is not feasible due to
a large number of model types resulting in O(n) queries. This setting
may not be compatible with non-standard deployments, and should only be
used when non-prefetched invocations would result in a large number of
queries or when latency is particularly important.

Defaults to `False`.

## `GUARDIAN_USER_OBJ_PERMS_MODEL`

!!! abstract "Added in version 2.0.0"

Allows the default `UserObjectPermission` model to be overridden by a
custom model. The custom model needs to minimally inherit from
`UserObjectPermissionAbstract`. This is only automatically supported
when set at the start of a project. This is NOT supported after the
start of a project. If the dependent libraries do not call
`UserObjectPermission = get_user_obj_perms_model()` for the model, then
the dependent library does not support this feature.

Define a custom user object permission model 

```python
from guardian.models import UserObjectPermissionAbstract

class BigUserObjectPermission(UserObjectPermissionAbstract):
id = models.BigAutoField(editable=False, unique=True, primary_key=True)

    class Meta(UserObjectPermissionAbstract.Meta):
        abstract = False
        indexes = [
            *UserObjectPermissionAbstract.Meta.indexes,
            models.Index(fields=['content_type', 'object_pk', 'user']),
        ]
```

Configure guardian to use the custom model in `settings.py` ::

```python
GUARDIAN_USER_OBJ_PERMS_MODEL = "myapp.BigUserObjectPermission"
```
    

To access the model use `get_user_obj_perms_model()` with no parameters

```python
from guardian.utils import get_user_obj_perms_model
UserObjectPermission = get_user_obj_perms_model()
```

Defaults to `'guardian.UserObjectPermission'`.

## `GUARDIAN_GROUP_OBJ_PERMS_MODEL`

!!! abstract "Added in version 2.0.0"

Allows the default `GroupObjectPermission` model to be overridden by a
custom model. The custom model needs to minimally inherit from
`GroupObjectPermissionAbstract`. This is only automatically supported
when set at the start of a project. This is NOT supported after the
start of a project. If the dependent libraries do not call
`GroupObjectPermission = get_user_obj_perms_model()` for the model, then
the dependent library does not support this feature.

Define a custom user object permission model:

```python
from guardian.models import GroupObjectPermissionAbstract

class BigGroupObjectPermission(GroupObjectPermissionAbstract):
    id = models.BigAutoField(editable=False, unique=True, primary_key=True)

    class Meta(GroupObjectPermissionAbstract.Meta):
        abstract = False
        indexes = [
            *GroupObjectPermissionAbstract.Meta.indexes,
            models.Index(fields=['content_type', 'object_pk', 'group']),
        ]
```

Configure guardian to use the custom model in settings.py
```python
GUARDIAN_GROUP_OBJ_PERMS_MODEL = 'myapp.BigGroupObjectPermission'
```

To access the model use `get_user_obj_perms_model()` with no parameters

```python
from guardian.utils import get_user_obj_perms_model
GroupObjectPermission = get_user_obj_perms_model()
```

Defaults to `'guardian.GroupObjectPermission'`.
