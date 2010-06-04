.. _check:

Check object permissions
========================

Once we have :ref:`assigned some permissions <assign>` we can get into detail
about verifying permissions of user or group.

Standard way
------------

Normally to check if Joe is permitted to change ``Site`` objects we do this by
calling ``has_perm`` method on an ``User`` instance::

    >>> joe.has_perm('sites.change_site')
    False

And for a specific ``Site`` instance we do the same but we pass ``site`` as
additional argument::

    >>> site = Site.objects.get_current()
    >>> joe.has_perm('sites.change_site', site)
    False

Lets assign permission and check again::

    >>> from guardian.shortcuts import assign
    >>> assign('sites.change_site', joe, site)
    <UserObjectPermission: example.com | joe | change_site>
    >>> joe = User.objects.get(username='joe')
    >>> joe.has_perm('sites.change_site', site)
    True

This uses backend we have specified at settings module (see
:ref:`configuration`). More on a backend itself can be found at
:class:`Backend's API <guardian.backends.ObjectPermissionBackend>`.

Inside views
------------

Besides of standard ``has_perm`` method ``django-guardian`` provides some useful
helpers for object permission checks.

get_perms
~~~~~~~~~

To check permissions we can use quick-and-dirty shortcut::

    >>> from guardian.shortcuts import get_perms
    >>>
    >>> joe = User.objects.get(username='joe')
    >>> site = Site.objects.get_current()
    >>>
    >>> 'change_site' in get_perms(joe, site)
    True


It is probably better to use standard ``has_perm`` method. But for ``Group``
instances it is not as easy and ``get_perms`` could be handy here as it accepts
both ``User`` and ``Group`` instances. And if we need to do some more work we
can use lower level ``ObjectPermissionChecker`` class which is described in next
section.

ObjectPermissionChecker
~~~~~~~~~~~~~~~~~~~~~~~

At the ``core`` module of ``django-guardian`` there is a 
:class:`guardian.core.ObjectPermissionChecker` which checks permission of
user/group for specific object. It caches results so it may be used at part of
codes where we check permissions more than once.

Let's see it in action::

    >>> joe = User.objects.get(username='joe')
    >>> site = Site.objects.get_current()
    >>> from guardian.core import ObjectPermissionChecker
    >>> checker = ObjectPermissionChecker(joe) # we can pass user or group
    >>> checker.has_perm('change_site', site)
    True
    >>> checker.has_perm('add_site', site) # no additional query made
    False
    >>> checker.get_perms(site)
    [u'change_site']

Inside templates
----------------

``django-guardian`` comes with special template tag
:func:`guardian.templatetags.guardian_tags.get_obj_perms` which can store object
permissions for a given user/group and instance pair. In order to use it we need
to put following inside a template::

    {% load guardian_tags %}

get_obj_perms
~~~~~~~~~~~~~

.. autofunction:: guardian.templatetags.guardian_tags.get_obj_perms
   :noindex:

