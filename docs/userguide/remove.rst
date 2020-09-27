.. _remove:

Remove object permissions
=========================

Removing object permissions is as easy as assigning them. Just instead of
:func:`guardian.shortcuts.assign_perm` we would use
:func:`guardian.shortcuts.remove_perm` function (it accepts same arguments).

Example
-------

Let's get back to our fellow Joe::

    >>> site = Site.object.get_current()
    >>> joe.has_perm('change_site', site)
    True

Now, simply remove this permission::

    >>> from guardian.shortcuts import remove_perm
    >>> remove_perm('change_site', joe, site)
    >>> joe = User.objects.get(username='joe')
    >>> joe.has_perm('change_site', site)
    False

