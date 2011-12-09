from django.contrib.auth.models import User
from django.db import models

from guardian.conf import settings
from guardian.exceptions import WrongAppError
from guardian.core import ObjectPermissionChecker

class ObjectPermissionBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True
    supports_inactive_user = True

    def authenticate(self, username, password):
        return None

    def has_perm(self, user_obj, perm, obj=None):
        """
        Returns ``True`` if given ``user_obj`` has ``perm`` for ``obj``. If no
        ``obj`` is given, ``False`` is returned.

        .. note::

           Remember, that if user is not *active*, all checks would return
           ``False``.

        Main difference between Django's ``ModelBackend`` is that we can pass
        ``obj`` instance here and ``perm`` doesn't have to contain
        ``app_label`` as it can be retrieved from given ``obj``.

        **Inactive user support**

        If user is authenticated but inactive at the same time, all checks
        always returns ``False``.
        """
        # Backend checks only object permissions
        if obj is None:
            return False

        # Backend checks only permissions for Django models
        if not isinstance(obj, models.Model):
            return False

        # This is how we support anonymous users - simply try to retrieve User
        # instance and perform checks for that predefined user
        if not user_obj.is_authenticated():
            user_obj = User.objects.get(pk=settings.ANONYMOUS_USER_ID)

        # Do not check any further if user is not active
        if not user_obj.is_active:
            return False

        if len(perm.split('.')) > 1:
            app_label, perm = perm.split('.')
            if app_label != obj._meta.app_label:
                raise WrongAppError("Passed perm has app label of '%s' and "
                    "given obj has '%s'" % (app_label, obj._meta.app_label))

        check = ObjectPermissionChecker(user_obj)
        return check.has_perm(perm, obj)

