"""
Implementation of per object permissions for Django.
"""
from __future__ import unicode_literals
from . import checks

default_app_config = 'guardian.apps.GuardianConfig'

# PEP 396: The __version__ attribute's value SHOULD be a string.
__version__ = '1.4.9'

# Compatibility to eg. django-rest-framework
VERSION = tuple(int(x) for x in __version__.split('.')[:3])


def get_version():
    return __version__


def monkey_patch_user():
    from .compat import get_user_model
    from .utils import get_anonymous_user
    from .models import UserObjectPermission
    User = get_user_model()
    # Prototype User and Group methods
    setattr(User, 'get_anonymous', staticmethod(lambda: get_anonymous_user()))
    setattr(User, 'add_obj_perm',
            lambda self, perm, obj: UserObjectPermission.objects.assign_perm(perm, self, obj))
    setattr(User, 'del_obj_perm',
            lambda self, perm, obj: UserObjectPermission.objects.remove_perm(perm, self, obj))
