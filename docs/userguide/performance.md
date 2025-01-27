---
title: Performance
description: Performance implications and optimizations when using django-guardian.
---

# Performance Tuning 

It is important to remember that by default `django-guardian` uses
generic foreign keys to retain relation with any Django model. For most
cases, it's probably good enough, however if we have a lot of queries
being spanned and our database seems to be choking it might be a good
choice to use *direct* foreign keys. Let's start with quick overview of
how generic solution work and then we will move on to the tuning part.

## Default, generic solution

`django-guardian` comes with two models: 
`UserObjectPermission` and `GroupObjectPermission`. They both have
same, generic way of pointing to other models:

-   `content_type` field telling what table (model class) target
    permission references to (`ContentType` instance)
-   `object_pk` field storing value of target model instance primary key
-   `content_object` field being a `GenericForeignKey`. Actually, it is
    not a foreign key in standard, relational database meaning - it is
    simply a proxy that can retrieve proper model instance being
    targeted by two previous fields

!!! tip "See Also"
    [Django generic relations](https://docs.djangoproject.com/en/stable/ref/contrib/contenttypes/#generic-relations)

Let's consider following model:

``` python
class Project(models.Model):
    name = models.CharField(max_length=128, unique=True)
```

To add a *change_project* permission for *joe* user we would
use `api-shortcuts-assign` shortcut:

``` python
>>> from guardian.shortcuts import assign_perm
>>> project = Project.objects.get(name='Foobar')
>>> joe = User.objects.get(username='joe')
>>> assign_perm('change_project', joe, project)
```

What it really does is: create an instance of
`UserObjectPermission`. Something
similar to:

``` python
>>> content_type = ContentType.objects.get_for_model(Project)
>>> perm = Permission.objects.get(content_type__app_label='app',
...     codename='change_project')
>>> UserObjectPermission.objects.create(user=joe, content_type=content_type,
...     permission=perm, object_pk=project.pk)
```

As there are no real foreign keys pointing at the target model, this
solution might not be enough for all cases. For example, if we try to
build an issues tracking service and we'd like to be able to support
thousands of users and their project/tickets, object level permission
checks can be slow with this generic solution.

## Direct foreign keys 

!!! abstract "Added in version 1.1"

To make our permission checks faster, we can use a direct foreign key.
It is straightforward to set up; 
All we need to do is to declare two new models next to our `Project` model,
one for `User` and one for `Group` models:

``` python
from guardian.models import UserObjectPermissionBase
from guardian.models import GroupObjectPermissionBase

class Project(models.Model):
    name = models.CharField(max_length=128, unique=True)

class ProjectUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Project, on_delete=models.CASCADE)

class ProjectGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Project, on_delete=models.CASCADE)
```

!!! danger "Important"
    Name of the `ForeignKey` field is important and it should be
    `content_object` as underlying queries depends on it.

From now on, `guardian` will figure out that `Project` model has direct
relation for user/group object permissions and will use those models. It
is also possible to use only user or only group-based direct relation,
however it is discouraged (it's not consistent and might be a quick
road to hell from the maintenance point of view, especially).

To temporarily disable the detection of this direct relation model, add
`enabled = False` to the object permission model classes. This is useful
to allow the ORM to create the tables for you and for you to migrate
data from the generic model tables before using the direct models.

!!! note
    By defining direct relation models we can also tweak that object
    permission model, i.e. by adding some fields.

## Prefetching permissions

!!! abstract "Added in version 1.4.3"

Naively looping through objects and checking permissions on each one
using `has_perms` results in a permissions lookup in the database for
each object. Large numbers of objects therefore produce large numbers of
database queries which can considerably slow down your app. To avoid
this, create an `ObjectPermissionChecker` and use its `prefetch_perms`
method before looping through the objects. This will do a single lookup
for all the objects and cache the results.

``` python
from guardian.core import ObjectPermissionChecker

joe = User.objects.get(username='joe')
projects = Project.objects.all()
checker = ObjectPermissionChecker(joe)

# Prefetch the permissions
checker.prefetch_perms(projects)

for project in projects:
    # No additional lookups needed to check permissions
    checker.has_perm('change_project', project)
```
