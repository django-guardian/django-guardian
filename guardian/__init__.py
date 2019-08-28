"""
Implementation of per object permissions for Django.
"""
from . import checks

default_app_config = 'guardian.apps.GuardianConfig'

# PEP 396: The __version__ attribute's value SHOULD be a string.
__version__ = '2.0.0'

# Compatibility to eg. django-rest-framework
VERSION = tuple(int(x) for x in __version__.split('.')[:3])


def get_version():
    return __version__


def monkey_patch_user():
    from django.contrib.auth import get_user_model
    from .utils import get_anonymous_user
    from .models import UserObjectPermission
    User = get_user_model()
    # Prototype User and Group methods
    setattr(User, 'get_anonymous', staticmethod(lambda: get_anonymous_user()))
    setattr(User, 'add_obj_perm',
            lambda self, perm, obj: UserObjectPermission.objects.assign_perm(perm, self, obj))
    setattr(User, 'del_obj_perm',
            lambda self, perm, obj: UserObjectPermission.objects.remove_perm(perm, self, obj))
    setattr(User, 'evict_obj_perm_cache', lambda self: delattr(self, '_guardian_perms_cache'))
