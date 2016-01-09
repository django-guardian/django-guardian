"""
Implementation of per object permissions for Django.
"""
from __future__ import unicode_literals
from . import checks

VERSION = (1, 4, 1)

__version__ = '.'.join((str(each) for each in VERSION[:4]))


def get_version():
    """
    Returns shorter version (digit parts only) as string.
    """
    return '.'.join((str(each) for each in VERSION[:4]))


default_app_config = 'guardian.apps.GuardianConfig'


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
