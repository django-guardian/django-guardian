---
title: Signals
description: How to react to object permission changes using Django signals.
---

# Reacting to Permission Changes with Signals

Django Guardian does not currently ship dedicated signals for permission changes.
However, you can use Django's built-in `post_save` and `post_delete` signals on
Guardian's permission models to react when object permissions are created or
removed.

## Connecting to Permission Model Signals

Guardian stores object permissions in `UserObjectPermission` and
`GroupObjectPermission` models (or your custom replacements). Because these are
regular Django models, you can connect to their `post_save` and `post_delete`
signals just like any other model.

Wire the signals inside your `AppConfig.ready()` method:

``` python
from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete


class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        from guardian.models import UserObjectPermission, GroupObjectPermission

        post_save.connect(self.handle_perm_change, sender=UserObjectPermission)
        post_save.connect(self.handle_perm_change, sender=GroupObjectPermission)
        post_delete.connect(self.handle_perm_change, sender=UserObjectPermission)
        post_delete.connect(self.handle_perm_change, sender=GroupObjectPermission)

    @staticmethod
    def handle_perm_change(sender, instance, **kwargs):
        # React to the permission change here.
        # For example: invalidate a cache, write an audit log, or send a
        # notification.
        print(f"Permission changed: {instance}")
```

!!! warning

    **Bulk operations do not fire `post_save` signals.** Methods like
    `bulk_assign_perm()` and `assign_perm_to_many()` use `bulk_create()`
    internally, so per-object `post_save` signals are not sent. If you rely on
    signals, assign permissions individually instead. See the
    [Assign Object Permissions](assign.md#limitations) page for details.

## Further Reading

This pattern was originally discussed in
[GitHub issue #805](https://github.com/django-guardian/django-guardian/issues/805).
