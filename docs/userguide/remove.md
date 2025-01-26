---
title: Removing Object Permissions
description: Removing object permissions from users and objects with django-guardian.
---

# Removing Object Permissions

Removing object permissions is as easy as assigning them. Just instead
of `guardian.shortcuts.assign_perm` we
would use `guardian.shortcuts.remove_perm` function (it accepts same arguments).

## Example

Let's get back to our fellow Joe:

```python
>>> site = Site.object.get_current()
>>> joe.has_perm('change_site', site)
True
```

Now, just remove this permission:

```python
>>> from guardian.shortcuts import remove_perm
>>> remove_perm('change_site', joe, site)
>>> joe = User.objects.get(username='joe')
>>> joe.has_perm('change_site', site)
False
```
