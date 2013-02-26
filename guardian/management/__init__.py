from __future__ import unicode_literals

import django
from django.db.models import signals

from guardian import models as guardian_app
from guardian.conf import settings as guardian_settings
from guardian.compat import get_user_model

def create_anonymous_user(sender, **kwargs):
    """
    Creates anonymous User instance with id and username from settings.
    """
    User = get_user_model()
    try:
        User.objects.get(pk=guardian_settings.ANONYMOUS_USER_ID)
    except User.DoesNotExist:
        if django.VERSION >= (1, 5):
            User.objects.create(pk=guardian_settings.ANONYMOUS_USER_ID,
                **{User.USERNAME_FIELD: guardian_settings.ANONYMOUS_DEFAULT_USERNAME_VALUE})
        else:
            User.objects.create(pk=guardian_settings.ANONYMOUS_USER_ID,
                username=guardian_settings.ANONYMOUS_DEFAULT_USERNAME_VALUE)

signals.post_syncdb.connect(create_anonymous_user, sender=guardian_app,
    dispatch_uid="guardian.management.create_anonymous_user")

