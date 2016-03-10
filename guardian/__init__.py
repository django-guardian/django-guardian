"""
Implementation of per object permissions for Django.
"""
from __future__ import unicode_literals
from . import checks


try:
    from .version import version as __version__
    __version__split__ = __version__.split(".")
    VERSION = tuple([int(each) for each in __version__split__[:3]] + __version__split__[3:])

    def get_version():
        """
        Returns shorter version (digit parts only) as string.
        """
        return '.'.join((str(each) for each in VERSION[:3]))
except ImportError:
    pass


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
