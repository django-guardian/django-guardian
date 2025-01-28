from django.contrib.auth import get_user_model
from django.db import models
from guardian.conf import settings
from guardian.core import ObjectPermissionChecker
from guardian.ctypes import get_content_type
from guardian.exceptions import WrongAppError


def check_object_support(obj):
    """Checks if given `obj` is supported

    Returns:
         supported (bool): `True` if given `obj` is supported
    """
    # Backend checks only object permissions (isinstance implies that obj
    # is not None)
    # Backend checks only permissions for Django models
    return isinstance(obj, models.Model)


def check_user_support(user_obj):
    """Checks if given user is supported.

    Checks if the given user is supported. Anonymous users need explicit
    activation via ANONYMOUS_USER_NAME

    Returns:
        results (tuple[bool, User]): A tuple of checkresult and `user_obj` which should be used for permission checks

    """
    # This is how we support anonymous users - simply try to retrieve User
    # instance and perform checks for that predefined user
    if not user_obj.is_authenticated:
        # If anonymous user permission is disabled then they are always
        # unauthorized
        if settings.ANONYMOUS_USER_NAME is None:
            return False, user_obj
        User = get_user_model()
        lookup = {User.USERNAME_FIELD: settings.ANONYMOUS_USER_NAME}
        user_obj = User.objects.get(**lookup)

    return True, user_obj


def check_support(user_obj, obj):
    """Checks if given user and object are supported.

    Combination of ``check_object_support`` and ``check_user_support``
    """
    obj_support = check_object_support(obj)
    user_support, user_obj = check_user_support(user_obj)
    return obj_support and user_support, user_obj


class ObjectPermissionBackend:
    """Django backend for checking object-level permissions."""
    supports_object_permissions = True
    supports_anonymous_user = True
    supports_inactive_user = True

    def authenticate(self, request, username=None, password=None):
        return None

    def has_perm(self, user_obj, perm, obj=None):
        """Check if a user has the permission for a given object.

        Returns `True` if given `user_obj` has `perm` for `obj`.
        If no `obj` is given, `False` is returned.
        The main difference between Django's `ModelBackend` is that we can pass
        `obj` instance here and `perm` doesn't have to contain
        `app_label` as it can be retrieved from given `obj`.

        **Inactive user support**

        If `user` is authenticated but inactive at the same time, all checks
        always return `False`.

        Note:
           Remember, that if user is not *active*, all checks would return `False`.

        Parameters:
            user_obj (User): User instance.
            perm (str): Permission string.
            obj (Model): Model instance.

        Returns:
            user_has_permission (bool): `True` if `user_obj` has permission, `False` otherwise.
        """

        # check if user_obj and object are supported
        support, user_obj = check_support(user_obj, obj)
        if not support:
            return False

        if '.' in perm:
            app_label, _ = perm.split('.', 1)
            if app_label != obj._meta.app_label:
                # Check the content_type app_label when permission
                # and obj app labels don't match.
                ctype = get_content_type(obj)
                if app_label != ctype.app_label:
                    raise WrongAppError("Passed perm has app label of '%s' while "
                                        "given obj has app label '%s' and given obj"
                                        "content_type has app label '%s'" %
                                        (app_label, obj._meta.app_label, ctype.app_label))

        check = ObjectPermissionChecker(user_obj)
        return check.has_perm(perm, obj)

    def get_all_permissions(self, user_obj, obj=None):
        """Returns all permissions for a given object.

        Parameters:
            user_obj (User): User instance.
            obj (Model): Django Model instance.

        Returns:
             permission (set): a set of permission strings that the given `user_obj` has for `obj`.
        """
        # check if user_obj and object are supported
        support, user_obj = check_support(user_obj, obj)
        if not support:
            return set()

        check = ObjectPermissionChecker(user_obj)
        return check.get_perms(obj)
