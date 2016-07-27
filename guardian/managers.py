from __future__ import unicode_literals

from django.db import models
from django.contrib.contenttypes.models import ContentType

from guardian.exceptions import ObjectNotPersisted
from guardian.models import Permission
from guardian.core import ObjectPermissionChecker
from django.db.models import Q
import warnings


class BaseObjectPermissionManager(models.Manager):

    @property
    def user_or_group_field(self):
        try:
            self.model._meta.get_field('user')
            return 'user'
        except models.fields.FieldDoesNotExist:
            return 'group'

    def is_generic(self):
        try:
            self.model._meta.get_field('object_pk')
            return True
        except models.fields.FieldDoesNotExist:
            return False

    def assign_perm(self, perm, user_or_group, obj):
        """
        Assigns permission with given ``perm`` for an instance ``obj`` and
        ``user``.
        """
        if getattr(obj, 'pk', None) is None:
            raise ObjectNotPersisted("Object %s needs to be persisted first"
                                     % obj)

        ctype = ContentType.objects.get_for_model(obj)
        if not isinstance(perm, Permission):
            permission = Permission.objects.get(content_type=ctype, codename=perm)
        else:
            permission = perm

        kwargs = {'permission': permission, self.user_or_group_field: user_or_group}
        if self.is_generic():
            kwargs['content_type'] = ctype
            kwargs['object_pk'] = obj.pk
        else:
            kwargs['content_object'] = obj
        obj_perm, _ = self.get_or_create(**kwargs)
        return obj_perm

    def bulk_assign_perm(self, perm, user_or_group, queryset):
        """
        Bulk assigns permissions with given ``perm`` for an objects in ``queryset`` and
        ``user_or_group``.
        """

        ctype = ContentType.objects.get_for_model(queryset.model)
        if not isinstance(perm, Permission):
            permission = Permission.objects.get(content_type=ctype, codename=perm)
        else:
            permission = perm

        checker = ObjectPermissionChecker(user_or_group)
        checker.prefetch_perms(queryset)

        assigned_perms = []
        for instance in queryset:
            if not checker.has_perm(permission.codename, instance):
                kwargs = {'permission': permission, self.user_or_group_field: user_or_group}
                if self.is_generic():
                    kwargs['content_type'] = ctype
                    kwargs['object_pk'] = instance.pk
                else:
                    kwargs['content_object'] = instance
                assigned_perms.append(self.model(**kwargs))
        self.model.objects.bulk_create(assigned_perms)

        return assigned_perms

    def assign(self, perm, user_or_group, obj):
        """ Depreciated function name left in for compatibility"""
        warnings.warn("UserObjectPermissionManager method 'assign' is being renamed to 'assign_perm'. Update your code accordingly as old name will be depreciated in 2.0 version.", DeprecationWarning)
        return self.assign_perm(perm, user_or_group, obj)

    def remove_perm(self, perm, user_or_group, obj):
        """
        Removes permission ``perm`` for an instance ``obj`` and given ``user_or_group``.

        Please note that we do NOT fetch object permission from database - we
        use ``Queryset.delete`` method for removing it. Main implication of this
        is that ``post_delete`` signals would NOT be fired.
        """
        if getattr(obj, 'pk', None) is None:
            raise ObjectNotPersisted("Object %s needs to be persisted first"
                                     % obj)

        filters = Q(**{self.user_or_group_field: user_or_group})

        if isinstance(perm, Permission):
            filters &= Q(permission=perm)
        else:
            filters &= Q(permission__codename=perm,
                         permission__content_type=ContentType.objects.get_for_model(obj))

        if self.is_generic():
            filters &= Q(object_pk=obj.pk)
        else:
            filters &= Q(content_object__pk=obj.pk)
        return self.filter(filters).delete()

    def bulk_remove_perm(self, perm, user_or_group, queryset):
        """
        Removes permission ``perm`` for a ``queryset`` and given ``user_or_group``.

        Please note that we do NOT fetch object permission from database - we
        use ``Queryset.delete`` method for removing it. Main implication of this
        is that ``post_delete`` signals would NOT be fired.
        """
        filters = Q(**{self.user_or_group_field: user_or_group})

        if self.is_generic():
            if isinstance(perm, Permission):
                filters &= Q(permission=perm)
            else:
                ctype = ContentType.objects.get_for_model(queryset.model)
                filters &= Q(permission__codename=perm,
                             permission__content_type=ctype)
        else:
            filters &= Q(content_object__in=queryset)

        return self.filter(filters).delete()


class UserObjectPermissionManager(BaseObjectPermissionManager):
    pass


class GroupObjectPermissionManager(BaseObjectPermissionManager):
    pass
