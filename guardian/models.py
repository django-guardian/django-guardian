from __future__ import unicode_literals

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

try:
    from django.contrib.contenttypes.fields import GenericForeignKey
except ImportError:
    from django.contrib.contenttypes.generic import GenericForeignKey

from django.utils.translation import ugettext_lazy as _

from guardian.compat import user_model_label
from guardian.compat import unicode
from guardian.conf import settings
from guardian.managers import GroupObjectPermissionManager
from guardian.managers import UserObjectPermissionManager


class BaseObjectPermission(models.Model):
    """
    Abstract ObjectPermission class. Actual class should additionally define
    a ``content_object`` field and either ``user`` or ``group`` field.
    """
    permission = models.ForeignKey(Permission)

    class Meta:
        abstract = True

    def __unicode__(self):
        return '%s | %s | %s' % (
            unicode(self.content_object),
            unicode(getattr(self, 'user', False) or self.group),
            unicode(self.permission.codename))

    def save(self, *args, **kwargs):
        content_type = ContentType.objects.get_for_model(self.content_object)
        if content_type != self.permission.content_type:
            raise ValidationError("Cannot persist permission not designed for "
                "this class (permission's type is %r and object's type is %r)"
                % (self.permission.content_type, content_type))
        return super(BaseObjectPermission, self).save(*args, **kwargs)


class BaseGenericObjectPermission(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_pk = models.CharField(_('object ID'), max_length=255)
    content_object = GenericForeignKey(fk_field='object_pk')

    class Meta:
        abstract = True


class UserObjectPermissionBase(BaseObjectPermission):
    """
    **Manager**: :manager:`UserObjectPermissionManager`
    """
    user = models.ForeignKey(user_model_label)

    objects = UserObjectPermissionManager()

    class Meta:
        abstract = True
        unique_together = ['user', 'permission', 'content_object']


class UserObjectPermission(UserObjectPermissionBase, BaseGenericObjectPermission):
    class Meta:
        unique_together = ['user', 'permission', 'object_pk']


class GroupObjectPermissionBase(BaseObjectPermission):
    """
    **Manager**: :manager:`GroupObjectPermissionManager`
    """
    group = models.ForeignKey(Group)

    objects = GroupObjectPermissionManager()

    class Meta:
        abstract = True
        unique_together = ['group', 'permission', 'content_object']


class GroupObjectPermission(GroupObjectPermissionBase, BaseGenericObjectPermission):
    class Meta:
        unique_together = ['group', 'permission', 'object_pk']


setattr(Group, 'add_obj_perm',
    lambda self, perm, obj: GroupObjectPermission.objects.assign_perm(perm, self, obj))
setattr(Group, 'del_obj_perm',
    lambda self, perm, obj: GroupObjectPermission.objects.remove_perm(perm, self, obj))
