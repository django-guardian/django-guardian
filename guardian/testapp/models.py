from __future__ import unicode_literals
from datetime import datetime
from django.db import models
from django.contrib.admin.models import LogEntry
from guardian.models import UserObjectPermissionBase, GroupObjectPermissionBase


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

