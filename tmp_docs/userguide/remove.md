# Remove object permissions {#remove}

Removing object permissions is as easy as assigning them. Just instead
of `guardian.shortcuts.assign_perm`{.interpreted-text role="func"} we
would use `guardian.shortcuts.remove_perm`{.interpreted-text
role="func"} function (it accepts same arguments).

## Example

Let\'s get back to our fellow Joe:

    >>> site = Site.object.get_current()
    >>> joe.has_perm('change_site', site)
    True

Now, simply remove this permission:

    >>> from guardian.shortcuts import remove_perm
    >>> remove_perm('change_site', joe, site)
    >>> joe = User.objects.get(username='joe')
    >>> joe.has_perm('change_site', site)
    False
