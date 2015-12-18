from __future__ import unicode_literals
from datetime import datetime

from django.db import models
from django.contrib.admin.models import LogEntry

from guardian.mixins import GuardianUserMixin
from guardian.models import UserObjectPermissionBase
from guardian.models import GroupObjectPermissionBase


class Post(models.Model):
    title = models.CharField('title', max_length=64)


class DynamicAccessor(object):
    def __init__(self):
        pass

    def __getattr__(self, key):
        return DynamicAccessor()


class ProjectUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey('Project')


class ProjectGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey('Project')


class Project(models.Model):
    name = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(default=datetime.now)

    class Meta:
        get_latest_by = 'created_at'

    def __unicode__(self):
        return self.name


Project.not_a_relation_descriptor = DynamicAccessor()


class MixedGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey('Mixed')


class Mixed(models.Model):
    """
    Model for tests obj perms checks with generic user object permissions model
    and direct group object permissions model.
    """
    name = models.CharField(max_length=128, unique=True)

    def __unicode__(self):
        return self.name


class LogEntryWithGroup(LogEntry):
    group = models.ForeignKey('auth.Group', null=True, blank=True)


class NonIntPKModel(models.Model):
    """
    Model for testing whether get_objects_for_user will work when the objects to
    be returned have non-integer primary keys.
    """
    char_pk = models.CharField(primary_key=True, max_length=128)


from django.contrib.auth.models import AbstractUser
class CustomUser(AbstractUser, GuardianUserMixin):
    custom_id = models.AutoField(primary_key=True)
