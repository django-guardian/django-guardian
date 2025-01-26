---
title: Caveats
description: Things to be aware of when using django-guardian.
---

# Caveats

There are a few things to be aware of when using django-guardian to manage object permissions.
If ignored, they can lead to unexpected behavior and potential security issues.

## Orphaned object permissions

Note the following does not apply if using direct foreign keys, as
documented in `performance-direct-fk`.

Permissions, in particular *per object permissions*, can be tricky to manage.
For example, how can we manage permissions that are no longer used?
In some setups, it is possible to reuse database primary keys 
which have been removed from the database. 
When permissions are at the model level only, this is not a problem;
but can lead to tremendous security issues when using object permissions.
How can we deal with this?

Let's imagine our table has primary key to the filesystem path.
We have a record with pk equal to `/home/www/joe.config`.
User *jane* has read access to joe's configuration and we store that information in database
by creating guardian's object permissions. 
Now, *joe* user removes account from our site and another user creates account with *joe* as username.
The problem is that if we haven't removed object permissions explicitly in 
the process of first *joe* account removal, *jane* still
has read permissions for *joe's* configuration file - but this is another user.

There is no easy way to deal with orphaned permissions as they are not
foreign keyed with objects directly. Even if they would, there are some
database engines—or *ON DELETE* rules—which restricts removal of
related objects.

!!! danger "Important"

    It is **extremely** important to remove`UserObjectPermission` and
    `GroupObjectPermission` as we delete objects for which permissions are defined.

Guardian comes with utility function which tries to help to remove
orphaned object permissions. Remember - those are only helpers.
Applications should remove those object permissions explicitly by
itself.

From our previous example, our application should remove a user object (e.g., *joe*). 
However, permissions for the *joe* user assigned to *jane* would**NOT** be removed. 
In this case, it would be easy to remove
user/group object permissions if we connect proper action with proper
signal. 
This could be achieved by following snippet:

```python
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Q
    from django.db.models.signals import pre_delete
    from guardian.models import User
    from guardian.models import UserObjectPermission
    from guardian.models import GroupObjectPermission


    def remove_obj_perms_connected_with_user(sender, instance, **kwargs):
        filters = Q(content_type=ContentType.objects.get_for_model(instance),
            object_pk=instance.pk)
        UserObjectPermission.objects.filter(filters).delete()
        GroupObjectPermission.objects.filter(filters).delete()

    pre_delete.connect(remove_obj_perms_connected_with_user, sender=User)
```

This signal handler would remove all object permissions connected with
user just before user is actually removed.

If we forgot to add such handlers, we may still remove orphaned object
permissions by using `clean_orphan_obj_perms` If our application uses
[celery](http://www.celeryproject.org/), it is also straightforward to remove
orphaned permissions periodically with `guardian.utils.clean_orphan_obj_perms` function. 
We would still **strongly** advise to remove orphaned object permissions explicitly 
(i.e., at view that confirms object removal or using signals as described above).

!!! info
    - `guardian.utils.clean_orphan_obj_perms`
    - `clean_orphan_obj_perms`

## Using multiple databases

This is not supported at present time due to a Django bug. See
[288](https://github.com/django-guardian/django-guardian/issues/288) and
[16281](https://code.djangoproject.com/ticket/16281).
