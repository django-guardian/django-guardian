from django.db import models
from guardian.models import UserObjectPermissionBase
from guardian.models import GroupObjectPermissionBase


class TestModel(models.Model):
    name = models.CharField(max_length=128)


class DirectUser(UserObjectPermissionBase):
    content_object = models.ForeignKey('TestDirectModel', on_delete=models.CASCADE)


class DirectGroup(GroupObjectPermissionBase):
    content_object = models.ForeignKey('TestDirectModel', on_delete=models.CASCADE)


class TestDirectModel(models.Model):
    name = models.CharField(max_length=128)
