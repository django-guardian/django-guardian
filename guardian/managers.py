from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Q
from guardian.core import ObjectPermissionChecker
from guardian.ctypes import get_content_type
from guardian.exceptions import ObjectNotPersisted
from django.contrib.auth.models import Permission

import warnings


class BaseObjectPermissionManager(models.Manager):

    @property
    def user_or_group_field(self):
        try:
            self.model._meta.get_field('user')
            return 'user'
        except FieldDoesNotExist:
            return 'group'

    def is_generic(self):
        try:
            self.model._meta.get_field('object_pk')
            return True
        except FieldDoesNotExist:
            return False

    def _get_perms(self, ctype, perms):
        perms_to_get = []
        permissions = []
        for perm in perms:
            if not isinstance(perm, Permission):
                perms_to_get.append(perm)
            else:
                permissions.append(perm)

        if len(perms_to_get):
            permissions.extend(
                list(
                    Permission.objects.filter(
                        content_type=ctype, codename__in=perms_to_get
                    ).all()
                )
            )

            # this is necessary to maintain the previous behaviour of raising a Permission.DoesNotExist exception
            for perm_codename in perms_to_get:
                for perm in permissions:
                    if perm.codename == perm_codename:
                        break
                else:
                    raise Permission.DoesNotExist

        return permissions

    def _update_kwargs_with_obj_info(self, kwargs, ctype, obj):
        if self.is_generic():
            kwargs['content_type'] = ctype
            kwargs['object_pk'] = obj.pk
        else:
            kwargs['content_object'] = obj

        return kwargs

    def _generate_create_kwargs(self, permission, ctype, obj=None, user_or_group=None):
        kwargs = {'permission': permission}
        if user_or_group:
            kwargs[self.user_or_group_field] = user_or_group
        if obj:
            kwargs = self._update_kwargs_with_obj_info(kwargs, ctype, obj)

        return kwargs

    def assign_perm(self, perm, user_or_group, obj):
        """
        Assigns permission with given ``perm`` for an instance ``obj`` and
        ``user``.
        """
        if getattr(obj, 'pk', None) is None:
            raise ObjectNotPersisted("Object %s needs to be persisted first"
                                     % obj)
        ctype = get_content_type(obj)
        permission = self._get_perms(ctype, [perm])[0]
        kwargs = self._generate_create_kwargs(permission, ctype, obj=obj, user_or_group=user_or_group)
        obj_perm, _ = self.get_or_create(**kwargs)
        return obj_perm

    def bulk_assign_perm(self, perm, user_or_group, queryset):
        """
        Bulk assigns permissions with given ``perm`` for an objects in ``queryset`` and
        ``user_or_group``.
        """
        if isinstance(queryset, list):
            ctype = get_content_type(queryset[0])
        else:
            ctype = get_content_type(queryset.model)

        permission = self._get_perms(ctype, [perm])[0]

        checker = ObjectPermissionChecker(user_or_group)
        checker.prefetch_perms(queryset)

        assigned_perms = []
        kwargs = self._generate_create_kwargs(permission, ctype, user_or_group=user_or_group)
        for instance in queryset:
            if not checker.has_perm(permission.codename, instance):
                assigned_perms.append(self.model(
                    **self._update_kwargs_with_obj_info(kwargs.copy(), ctype, obj=instance)
                ))
        self.model.objects.bulk_create(assigned_perms)

        return assigned_perms

    def assign_perm_to_many(self, perm, users_or_groups, obj):
        """
        Bulk assigns given ``perm`` for the object ``obj`` to a set of users or a set of groups.
        """
        ctype = get_content_type(obj)
        permission = self._get_perms(ctype, [perm])[0]

        kwargs = self._generate_create_kwargs(permission, ctype, obj=obj)
        to_add = []
        field = self.user_or_group_field
        for user in users_or_groups:
            kwargs[field] = user
            to_add.append(
                self.model(**kwargs)
            )

        return self.model.objects.bulk_create(to_add)

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
                         permission__content_type=get_content_type(obj))

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

        if isinstance(perm, Permission):
            filters &= Q(permission=perm)
        else:
            ctype = get_content_type(queryset.model)
            filters &= Q(permission__codename=perm,
                         permission__content_type=ctype)

        if self.is_generic():
            filters &= Q(object_pk__in=[str(pk) for pk in queryset.values_list('pk', flat=True)])
        else:
            filters &= Q(content_object__in=queryset)

        return self.filter(filters).delete()


class UserObjectPermissionManager(BaseObjectPermissionManager):
    pass


class GroupObjectPermissionManager(BaseObjectPermissionManager):
    pass
