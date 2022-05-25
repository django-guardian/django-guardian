from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Q, CharField
from django.db.models.functions import Cast
from django.db.models.query import QuerySet
from guardian.core import ObjectPermissionChecker
from guardian.ctypes import get_content_type, get_content_type_from_iterable_or_object
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

    def _retrieve_perms(self, ctype, perms):
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

    def _get_obj_list(self, queryset):
        if isinstance(queryset, list):
            objs = queryset
        elif isinstance(queryset, QuerySet):
            objs = list(queryset)
        else:
            objs = [queryset]

        return objs

    def assign_perm(self, perm, user_or_group, obj):
        """
        Assigns permission with given ``perm`` for an instance ``obj`` and
        ``user``.

        Note this has not been refactored to use self.assign_perms_to_many_for_many, since it behaves differently in
        tests. Essentially, due to the fact that it uses get_or_create, rather than bulk_create, here we sometimes
        create guardian permissions for users who already "have the permission" (eg. superusers, who have permissions
        without needing to be assigned them).
        """
        if getattr(obj, 'pk', None) is None:
            raise ObjectNotPersisted("Object %s needs to be persisted first"
                                     % obj)
        ctype = get_content_type_from_iterable_or_object(obj)
        permission = self._retrieve_perms(ctype, [perm])[0]
        kwargs = self._generate_create_kwargs(permission, ctype, obj=obj, user_or_group=user_or_group)
        obj_perm, _ = self.get_or_create(**kwargs)
        return obj_perm

    def bulk_assign_perm(self, perm, user_or_group, queryset):
        """
        Bulk assigns permissions with given ``perm`` for an objects in ``queryset`` and
        ``user_or_group``.
        """
        return self.assign_perms_to_many_for_many(
            [perm],
            [user_or_group],
            queryset
        )

    def assign_perm_to_many(self, perm, users_or_groups, obj):
        """
        Bulk assigns given ``perm`` for the object ``obj`` to a set of users or a set of groups.
        """
        return self.assign_perms_to_many_for_many(
            [perm],
            users_or_groups,
            obj
        )

    def assign_perms_to_many_for_many(self, perms, users_or_groups, queryset, commit=True):
        """
        Bulk assigns given ``perms`` for all objects ``obj`` to a set of users or a set of groups.
        """
        ctype = get_content_type_from_iterable_or_object(queryset)
        permissions = self._retrieve_perms(ctype, perms)
        objects = self._get_obj_list(queryset)

        to_add = []
        for user_or_group in users_or_groups:
            checker = ObjectPermissionChecker(user_or_group)
            checker.prefetch_perms(objects)

            for permission in permissions:
                kwargs = self._generate_create_kwargs(permission, ctype, user_or_group=user_or_group)
                for obj in objects:
                    if not checker.has_perm(permission.codename, obj):
                        to_add.append(self.model(
                            **self._update_kwargs_with_obj_info(kwargs.copy(), ctype, obj=obj)
                        ))

        if commit:
            return self.model.objects.bulk_create(to_add)
        else:
            return to_add

    def assign(self, perm, user_or_group, obj):
        """ Depreciated function name left in for compatibility"""
        warnings.warn("UserObjectPermissionManager method 'assign' is being renamed to 'assign_perm'. Update your code accordingly as old name will be depreciated in 2.0 version.", DeprecationWarning)
        return self.assign_perm(perm, user_or_group, obj)

    def _get_base_filters(self, users_or_groups, iterable_or_object):
        filters = Q(**{"%s__in" % self.user_or_group_field: users_or_groups})

        if isinstance(iterable_or_object, (list, QuerySet)):
            queryset = iterable_or_object
            if self.is_generic():
                filters &= Q(
                    # we have to do this cast, otherwise postgres errors
                    object_pk__in=queryset.annotate(
                        pk_as_char=Cast("pk", CharField())
                    ).values_list("pk_as_char", flat=True)
                    if isinstance(queryset, QuerySet)
                    else [obj.pk for obj in queryset]
                )
            else:
                filters &= Q(content_object__in=queryset)
        else:
            obj = iterable_or_object
            if self.is_generic():
                filters &= Q(object_pk=obj.pk)
            else:
                filters &= Q(content_object__pk=obj.pk)

        return filters

    def _get_filters_for_perm(self, perm, ctype, filters):
        if isinstance(perm, Permission):
            filters &= Q(permission=perm)
        else:
            filters &= Q(permission__codename=perm,
                         permission__content_type=ctype)

        return filters

    def _remove_perms(self, perms, users_or_groups, iterable_or_object, ctype, commit=True):
        """
        Note that while ctype is technically discoverable from queryset_or_object, we enforce passing it in, since
        dynamically determing it goes against past behaviour of the exposed functions which call this method.
        """
        filters = self._get_base_filters(users_or_groups, iterable_or_object)
        disjunction_cond = Q()

        for perm in perms:
            conjunction_cond = Q()
            conjunction_cond = self._get_filters_for_perm(perm, ctype, conjunction_cond)
            disjunction_cond |= conjunction_cond

        filters &= disjunction_cond

        if commit:
            return self.filter(filters).delete()
        else:
            return self.filter(filters).all()

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

        return self._remove_perms([perm], [user_or_group], obj, get_content_type(obj))

    def bulk_remove_perm(self, perm, user_or_group, queryset):
        """
        Removes permission ``perm`` for a ``queryset`` and given ``user_or_group``.

        Please note that we do NOT fetch object permission from database - we
        use ``Queryset.delete`` method for removing it. Main implication of this
        is that ``post_delete`` signals would NOT be fired.
        """
        return self._remove_perms([perm], [user_or_group], queryset, get_content_type(queryset.model))

    def bulk_remove_perms(self, perms, user_or_group_or_iterable, iterable_or_object, commit=True):
        """
        Allows removing multiple perms for multiple users_or_groups for multiple objects.
        Also supports passing in a single object for users_or_groups and for queryset_or_object

        Please note that we do NOT fetch object permission from database - we
        use ``Queryset.delete`` method for removing it. Main implication of this
        is that ``post_delete`` signals would NOT be fired.
        """

        ctype = get_content_type_from_iterable_or_object(iterable_or_object)
        if isinstance(user_or_group_or_iterable, (list, QuerySet)):
            users_or_groups = user_or_group_or_iterable
        else:
            users_or_groups = [user_or_group_or_iterable]

        return self._remove_perms(perms, users_or_groups, iterable_or_object, ctype, commit=commit)


class UserObjectPermissionManager(BaseObjectPermissionManager):
    pass


class GroupObjectPermissionManager(BaseObjectPermissionManager):
    pass
