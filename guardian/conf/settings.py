from __future__ import unicode_literals
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

ANONYMOUS_DEFAULT_USERNAME_VALUE = getattr(settings,
    'ANONYMOUS_DEFAULT_USERNAME_VALUE', 'AnonymousUser')

try:
    ANONYMOUS_USER_ID = settings.ANONYMOUS_USER_ID
except AttributeError:
    raise ImproperlyConfigured("In order to use django-guardian's "
        "ObjectPermissionBackend authorization backend you have to configure "
        "ANONYMOUS_USER_ID at your settings module")

RENDER_403 = getattr(settings, 'GUARDIAN_RENDER_403', False)
TEMPLATE_403 = getattr(settings, 'GUARDIAN_TEMPLATE_403', '403.html')
RAISE_403 = getattr(settings, 'GUARDIAN_RAISE_403', False)
GET_INIT_ANONYMOUS_USER = getattr(settings, 'GUARDIAN_GET_INIT_ANONYMOUS_USER',
    'guardian.management.get_init_anonymous_user')

MONKEY_PATCH = getattr(settings, 'GUARDIAN_MONKEY_PATCH', True)

def check_configuration():
    if RENDER_403 and RAISE_403:
        raise ImproperlyConfigured("Cannot use both GUARDIAN_RENDER_403 AND "
            "GUARDIAN_RAISE_403 - only one of this config may be True")

check_configuration()

