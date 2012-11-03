from django.db import models
from django.contrib.contenttypes.models import ContentType

from guardian.exceptions import ObjectNotPersisted
from guardian.models import Permission

class UserObjectPermissionManager(models.Manager):

    def assign(self, perm, user, obj):
        """
        Assigns permission with given ``perm`` for an instance ``obj`` and
        ``user``.
        """
        if getattr(obj, 'pk', None) is None:
            raise ObjectNotPersisted("Object %s needs to be persisted first"
                % obj)
        ctype = ContentType.objects.get_for_model(obj)
        permission = Permission.objects.get(
            content_type=ctype, codename=perm)

        obj_perm, created = self.get_or_create(
            content_type = ctype,
            permission = permission,
            object_pk = obj.pk,
            user = user)
        return obj_perm

    def remove_perm(self, perm, user, obj):
        """
        Removes permission ``perm`` for an instance ``obj`` and given ``user``.
        """
        if getattr(obj, 'pk', None) is None:
            raise ObjectNotPersisted("Object %s needs to be persisted first"
                % obj)
        self.filter(
            permission__codename=perm,
            user=user,
            object_pk=obj.pk,
            content_type=ContentType.objects.get_for_model(obj))\
            .delete()

    def get_for_object(self, user, obj):
        if getattr(obj, 'pk', None) is None:
            raise ObjectNotPersisted("Object %s needs to be persisted first"
                % obj)
        ctype = ContentType.objects.get_for_model(obj)
        perms = self.filter(
            content_type = ctype,
            user = user,
        )
        return perms

class GroupObjectPermissionManager(models.Manager):

    def assign(self, perm, group, obj):
        """
        Assigns permission with given ``perm`` for an instance ``obj`` and
        ``group``.
        """
        if getattr(obj, 'pk', None) is None:
            raise ObjectNotPersisted("Object %s needs to be persisted first"
                % obj)
        ctype = ContentType.objects.get_for_model(obj)
        permission = Permission.objects.get(
            content_type=ctype, codename=perm)

        obj_perm, created = self.get_or_create(
            content_type = ctype,
            permission = permission,
            object_pk = obj.pk,
            group = group)
        return obj_perm

    def remove_perm(self, perm, group, obj):
        """
        Removes permission ``perm`` for an instance ``obj`` and given ``group``.
        """
        if getattr(obj, 'pk', None) is None:
            raise ObjectNotPersisted("Object %s needs to be persisted first"
                % obj)
        self.filter(
            permission__codename=perm,
            group=group,
            object_pk=obj.pk,
            content_type=ContentType.objects.get_for_model(obj))\
            .delete()

    def get_for_object(self, group, obj):
        if getattr(obj, 'pk', None) is None:
            raise ObjectNotPersisted("Object %s needs to be persisted first"
                % obj)
        ctype = ContentType.objects.get_for_model(obj)
        perms = self.filter(
            content_type = ctype,
            group = group,
        )
        return perms

