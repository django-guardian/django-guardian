.. _caveats:

Caveats
=======

Orphaned object permissions
---------------------------

Permissions, including so called *per object permissions*, are sometimes tricky
to manage. One case is how we can manage permissions that are no longer used.
Normally, there should be no problems, however with some particular setup it is
possible to reuse primary keys of database models which were used in the past
once. We will not answer how bad such situation can be - instead we will try to
cover how we can deal with this.

Let's imagine our table has primary key to the filesystem path. We have a record
with pk equal to ``/home/www/joe.config``. User *jane* has read access to
joe's configuration and we store that information in database by creating
guardian's object permissions. Now, *joe* user removes account from our site and
another user creates account with *joe* as username. The problem is that if we
haven't removed object permissions explicitly in the process of first *joe*
account removal, *jane* still has read permissions for *joe's* configuration
file - but this is another user.

There is no easy way to deal with orphaned permissions as they are not foreign
keyed with objects directly. Even if they would, there are some database engines
- or *ON DELETE* rules - which restricts removal of related objects.

.. important::

   It is **extremely** important to remove :model:`UserObjectPermission` and
   :model:`GroupObjectPermission` as we delete objects for which permissions
   are defined.

Guardian comes with utility function which tries to help to remove orphaned
object permissions. Remember - those are only helpers. Applications should
remove those object permissions explicitly by itself.

Taking our previous example, our application should remove user object for
*joe*, however, permisions for *joe* user assigned to *jane* would **NOT**
be removed. In this case, it would be very easy to remove user/group object
permissions if we connect proper action with proper signal. This could be
achieved by following snippet::

    from django.contrib.auth.models import User
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Q
    from django.db.models.signals import pre_delete
    from guardian.models import UserObjectPermission
    from guardian.models import GroupObjectPermission


    def remove_obj_perms_connected_with_user(sender, instance, **kwargs):
        filters = Q(content_type=ContentType.objects.get_for_model(instance),
            object_pk=instance.pk)
        UserObjectPermission.objects.filter(filters).delete()
        GroupObjectPermission.objects.filter(filters).delete()

    pre_delete.connect(remove_obj_perms_connected_with_user, sender=User)


This signal handler would remove all object permissions connected with user
just before user is actually removed.

If we forgot to add such handlers, we may still remove orphaned object
permissions by using :command:`clean_orphan_obj_perms` command. If our
application uses celery_, it is also very easy to remove orphaned permissions
periodically with :func:`guardian.utils.clean_orphan_obj_perms` function.
We would still **strongly** advise to remove orphaned object permissions
explicitly (i.e. at view that confirms object removal or using signals as
described above).

.. seealso::

   - :func:`guardian.utils.clean_orphan_obj_perms`
   - :command:`clean_orphan_obj_perms`

.. _celery: http://www.celeryproject.org/

