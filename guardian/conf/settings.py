from __future__ import unicode_literals
import warnings
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

ANONYMOUS_USER_NAME = getattr(settings, 'ANONYMOUS_USER_NAME', None)

if ANONYMOUS_USER_NAME is None:
    ANONYMOUS_USER_NAME = getattr(settings, 'ANONYMOUS_DEFAULT_USERNAME_VALUE', None)
    if ANONYMOUS_USER_NAME is not None:
        warnings.warn("The ANONYMOUS_DEFAULT_USERNAME_VALUE setting has been renamed to ANONYMOUS_USER_NAME.", DeprecationWarning)

if ANONYMOUS_USER_NAME is None:
    ANONYMOUS_USER_NAME = 'AnonymousUser'

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
