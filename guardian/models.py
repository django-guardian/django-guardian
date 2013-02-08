
import django
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _

from guardian.conf import settings as guardian_settings
from guardian.managers import GroupObjectPermissionManager
from guardian.managers import UserObjectPermissionManager

# Django 1.5+ compatibility
if django.VERSION >= (1, 5):
    from django.contrib.auth import get_user_model
    User = get_user_model()
else:
    from django.contrib.auth.models import User


__all__ = ['BaseObjectPermission', 'UserObjectPermission',
    'GroupObjectPermission', 'UserObjectPermissionManager',
    'GroupObjectPermissionManager', 'User', 'Group', 'Permission',
    'AnonymousUser']


class BaseObjectPermission(models.Model):
    """
    Abstract ObjectPermission class.
    """
    permission = models.ForeignKey(Permission)

    content_type = models.ForeignKey(ContentType)
    object_pk = models.CharField(_('object ID'), max_length=255)
    content_object = generic.GenericForeignKey(fk_field='object_pk')

    class Meta:
        abstract = True

    def __unicode__(self):
        return u'%s | %s | %s' % (
            unicode(self.content_object),
            unicode(getattr(self, 'user', False) or self.group),
            unicode(self.permission.codename))

    def save(self, *args, **kwargs):
        if self.content_type != self.permission.content_type:
            raise ValidationError("Cannot persist permission not designed for "
                "this class (permission's type is %s and object's type is %s)"
                % (self.permission.content_type, self.content_type))
        return super(BaseObjectPermission, self).save(*args, **kwargs)


class UserObjectPermission(BaseObjectPermission):
    """
    **Manager**: :manager:`UserObjectPermissionManager`
    """
    user = models.ForeignKey(getattr(django.conf.settings, 'AUTH_USER_MODEL', 'auth.User'))

    objects = UserObjectPermissionManager()

    class Meta:
        unique_together = ['user', 'permission', 'content_type', 'object_pk']


class GroupObjectPermission(BaseObjectPermission):
    """
    **Manager**: :manager:`GroupObjectPermissionManager`
    """
    group = models.ForeignKey(Group)

    objects = GroupObjectPermissionManager()

    class Meta:
        unique_together = ['group', 'permission', 'content_type', 'object_pk']


# Prototype User and Group methods
setattr(User, 'get_anonymous', staticmethod(lambda: get_anonymous_user()))
setattr(User, 'add_obj_perm',
    lambda self, perm, obj: UserObjectPermission.objects.assign(perm, self, obj))
setattr(User, 'del_obj_perm',
    lambda self, perm, obj: UserObjectPermission.objects.remove_perm(perm, self, obj))

setattr(Group, 'add_obj_perm',
    lambda self, perm, obj: GroupObjectPermission.objects.assign(perm, self, obj))
setattr(Group, 'del_obj_perm',
    lambda self, perm, obj: GroupObjectPermission.objects.remove_perm(perm, self, obj))