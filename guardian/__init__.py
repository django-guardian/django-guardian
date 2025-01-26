"""
Implementation of per object permissions for Django.
"""
from . import checks
from importlib.metadata import version

import re

# Use importlib to ensure this version always matches with pyproject.toml
__version__ = version('django-guardian')

# Compatibility to eg. django-rest-framework
# (removes any release candidate or other modifiers)
VERSION = tuple(int(x) for x in re.split('[a-z]', __version__)[0].split('.')[:3])

def get_version():
    return __version__


def monkey_patch_user():
    from .utils import evict_obj_perms_cache, get_anonymous_user, get_user_obj_perms_model
    from django.contrib.auth import get_user_model
    UserObjectPermission = get_user_obj_perms_model()
    User = get_user_model()
    # Prototype User and Group methods
    setattr(User, 'get_anonymous', staticmethod(lambda: get_anonymous_user()))
    setattr(User, 'add_obj_perm',
            lambda self, perm, obj: UserObjectPermission.objects.assign_perm(perm, self, obj))
    setattr(User, 'del_obj_perm',
            lambda self, perm, obj: UserObjectPermission.objects.remove_perm(perm, self, obj))
    setattr(User, 'evict_obj_perms_cache', evict_obj_perms_cache)


def monkey_patch_group():
    from .utils import get_group_obj_perms_model
    from django.contrib.auth.models import Group, Permission

    GroupObjectPermission = get_group_obj_perms_model()
    # Prototype Group methods
    setattr(Group, 'add_obj_perm',
            lambda self, perm, obj: GroupObjectPermission.objects.assign_perm(perm, self, obj))
    setattr(Group, 'del_obj_perm',
            lambda self, perm, obj: GroupObjectPermission.objects.remove_perm(perm, self, obj))
