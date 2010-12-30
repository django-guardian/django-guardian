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
remove those object permissions explicitly.

.. seealso::

   - :func:`guardian.utils.clean_orphan_obj_perms`
   - :command:`clean_orphan_obj_perms`

