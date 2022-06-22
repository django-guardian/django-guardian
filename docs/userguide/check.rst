.. _check:

Check object permissions
========================

Once we have :ref:`assigned some permissions <assign>`, we can get into detail
about verifying permissions of a user or group.

Standard way
------------

Normally to check if Joe is permitted to change ``Site`` objects we
call ``has_perm`` method on an ``User`` instance::

    >>> joe.has_perm('sites.change_site')
    False

And for a specific ``Site`` instance we do the same but we pass ``site`` as
additional argument::

    >>> site = Site.objects.get_current()
    >>> joe.has_perm('sites.change_site', site)
    False

Let's assign permission and check again::

    >>> from guardian.shortcuts import assign_perm
    >>> assign_perm('sites.change_site', joe, site)
    <UserObjectPermission: example.com | joe | change_site>
    >>> joe = User.objects.get(username='joe')
    >>> joe.has_perm('sites.change_site', site)
    True

This uses the backend we have specified at settings module (see
:ref:`configuration`). More on the backend can be found at
:class:`Backend's API <guardian.backends.ObjectPermissionBackend>`.

Inside views
------------

Aside from the standard ``has_perm`` method, ``django-guardian``
provides some useful helpers for object permission checks.

get_perms
~~~~~~~~~

To check permissions we can use a quick-and-dirty shortcut::

    >>> from guardian.shortcuts import get_perms
    >>>
    >>> joe = User.objects.get(username='joe')
    >>> site = Site.objects.get_current()
    >>>
    >>> 'change_site' in get_perms(joe, site)
    True


It is probably better to use standard ``has_perm`` method. But for ``Group``
instances it is not as easy and ``get_perms`` could be handy here as it accepts
both ``User`` and ``Group`` instances. If we need to do some more work, we
can use lower level ``ObjectPermissionChecker`` class which is described in 
the next section.

There is also ``get_user_perms`` to get permissions assigned directly to the user
(and not inherited from its superuser status or group membership).
Similarly, ``get_group_perms`` returns only permissions which are inferred
through user's group membership.
``get_user_perms`` and ``get_group_perms`` are useful when you care what permissions
user has assigned, while ``has_perm`` is useful when you care about user's effective
permissions.

get_objects_for_user
~~~~~~~~~~~~~~~~~~~~

Sometimes there is a need to extract list of objects based on particular user,
type of the object and provided permissions. For instance, lets say there is a
``Project`` model at ``projects`` application with custom ``view_project``
permission. We want to show our users projects they can actually *view*. This
could be easily achieved using :shortcut:`get_objects_for_user`:

.. code-block:: python

    from django.shortcuts import render
    from django.template import RequestContext
    from projects.models import Project
    from guardian.shortcuts import get_objects_for_user

    def user_dashboard(request, template_name='projects/dashboard.html'):
        projects = get_objects_for_user(request.user, 'projects.view_project')
        return render(request, template_name, {'projects': projects},
            RequestContext(request))

It is also possible to provide list of permissions rather than single string,
own queryset (as ``klass`` argument) or control if result should be computed
with (default) or without user's groups permissions.

.. seealso::
   Documentation for :shortcut:`get_objects_for_user`


ObjectPermissionChecker
~~~~~~~~~~~~~~~~~~~~~~~

At the ``core`` module of ``django-guardian``, there is a 
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

Using decorators
~~~~~~~~~~~~~~~~

Standard ``permission_required`` decorator doesn't allow to check for object
permissions. ``django-guardian`` is shipped with two decorators which may be
helpful for simple object permission checks but remember that those decorators
hits database before decorated view is called - this means that if there is
similar lookup made within a view then most probably one (or more, depending
on lookups) extra database query would occur.

Let's assume we pass ``'group_name'`` argument to our view function which
returns form to edit the group. Moreover, we want to return 403 code if check
fails. This can be simply achieved using ``permission_required_or_403``
decorator::

    >>> joe = User.objects.get(username='joe')
    >>> foobars = Group.objects.create(name='foobars')
    >>>
    >>> from guardian.decorators import permission_required_or_403
    >>> from django.http import HttpResponse
    >>>
    >>> @permission_required_or_403('auth.change_group',
    >>>     (Group, 'name', 'group_name'))
    >>> def edit_group(request, group_name):
    >>>     return HttpResponse('some form')
    >>>
    >>> from django.http import HttpRequest
    >>> request = HttpRequest()
    >>> request.user = joe
    >>> edit_group(request, group_name='foobars')
    <django.http.HttpResponseForbidden object at 0x102b43dd0>
    >>>
    >>> joe.groups.add(foobars)
    >>> edit_group(request, group_name='foobars')
    <django.http.HttpResponseForbidden object at 0x102b43e50>
    >>>
    >>> from guardian.shortcuts import assign_perm
    >>> assign_perm('auth.change_group', joe, foobars)
    <UserObjectPermission: foobars | joe | change_group>
    >>>
    >>> edit_group(request, group_name='foobars')
    <django.http.HttpResponse object at 0x102b8c8d0>
    >>> # Note that we now get normal HttpResponse, not forbidden

More on decorators can be read at corresponding :ref:`API page <api-decorators>`.

.. note::
   Overall idea of decorators' lookups was taken from `django-authority`_ and
   all credits go to it's creator, Jannis Leidel.

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

.. _django-authority: https://github.com/jazzband/django-authority

