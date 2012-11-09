
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _

from guardian.compat import AnonymousUser
from guardian.compat import Group
from guardian.compat import Permission
from guardian.compat import User
from guardian.managers import GroupObjectPermissionManager
from guardian.managers import UserObjectPermissionManager
from guardian.utils import get_anonymous_user


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
    user = models.ForeignKey(User)

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

