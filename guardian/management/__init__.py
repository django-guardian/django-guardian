from __future__ import unicode_literals

import django
from django.db.models import signals

from guardian import models as guardian_app
from guardian.conf import settings as guardian_settings
from guardian.compat import get_user_model
from guardian.compat import import_string


def get_init_anonymous_user(User):
    """
    Returns User model instance that would be referenced by guardian when
    permissions are checked against users that haven't signed into the system.

    :param User: User model - result of ``django.contrib.auth.get_user_model``.
    """
    kwargs = {
        User.USERNAME_FIELD: guardian_settings.ANONYMOUS_DEFAULT_USERNAME_VALUE
    }
    return User(**kwargs)


def create_anonymous_user(sender, **kwargs):
    """
    Creates anonymous User instance with id and username from settings.
    """
    User = get_user_model()
    try:
        User.objects.get(pk=guardian_settings.ANONYMOUS_USER_ID)
    except User.DoesNotExist:
        if django.VERSION >= (1, 5):
            retrieve_anonymous_function = import_string(
                guardian_settings.GET_INIT_ANONYMOUS_USER)
            user = retrieve_anonymous_function(User)
            # Always set pk to the one pointed at settings
            user.pk = guardian_settings.ANONYMOUS_USER_ID
            user.save()
        else:
            User.objects.create(pk=guardian_settings.ANONYMOUS_USER_ID,
                username=guardian_settings.ANONYMOUS_DEFAULT_USERNAME_VALUE)

# Only create an anonymous user if support is enabled.
if guardian_settings.ANONYMOUS_USER_ID is not None:
    signals.post_syncdb.connect(create_anonymous_user, sender=guardian_app,
        dispatch_uid="guardian.management.create_anonymous_user")
