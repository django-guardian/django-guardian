from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

ANONYMOUS_USER_ID = getattr(settings, 'ANONYMOUS_USER_ID', None)
if ANONYMOUS_USER_ID is None:
    raise ImproperlyConfigured("In order to use django-guardian's "
        "ObjectPermissionBackend authorization backend you have to configure "
        "ANONYMOUS_USER_ID at your settings module")

