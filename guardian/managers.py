from typing import Any, TypeAlias, Union
import warnings

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Model, Q, QuerySet

from guardian.conf import settings as guardian_settings
from guardian.core import ObjectPermissionChecker
from guardian.ctypes import get_content_type
from guardian.exceptions import ObjectNotPersisted

_PermType: TypeAlias = Union[Permission, str]

_DEFAULT_CONTENT_TYPE_PATH = "guardian.ctypes.get_default_content_type"


def _is_using_default_content_type() -> bool:
    """Check if default content type function is being used.

    Returns True if GUARDIAN_GET_CONTENT_TYPE setting points to the default
    get_default_content_type function, False otherwise.

    The check is necessary to avoid a regression where setting content_object
    in get_or_create defaults causes Django's GenericForeignKey.__set__ to
    overwrite the content_type that was explicitly set by a custom
    GUARDIAN_GET_CONTENT_TYPE function.

    Note: This function is not cached to allow dynamic changes during testing
    (e.g., when using mock.patch).
    """
    return guardian_settings.GET_CONTENT_TYPE == _DEFAULT_CONTENT_TYPE_PATH


def _ensure_permission(perm: _PermType, ctype: ContentType) -> Permission:
    if isinstance(perm, str):
        perm = Permission.objects.get(content_type=ctype, codename=perm)

    return perm


def _get_perm_filter(
    perm: _PermType, model: Union[Model, type[Model], None] = None, ctype: Union[ContentType, None] = None
) -> Q:
    if isinstance(perm, Permission):
        return Q(permission=perm)

    assert ctype is not None or model is not None
    if ctype is None and model is not None:
        ctype = get_content_type(model)

    return Q(permission__codename=perm, permission__content_type=ctype)


class BaseObjectPermissionManager(models.Manager):
    @property
    def user_or_group_field(self) -> str:
        try:
            self.model._meta.get_field("user")
            return "user"
        except FieldDoesNotExist:
            return "group"

    def is_generic(self) -> bool:
        try:
            self.model._meta.get_field("object_pk")
            return True
        except FieldDoesNotExist:
            return False

    def assign_perm(self, perm: _PermType, user_or_group: Any, obj: Model) -> Any:
        """Assigns permission with given `perm` for an instance `obj` and `user`."""
        if getattr(obj, "pk", None) is None:
            raise ObjectNotPersisted("Object %s needs to be persisted first" % obj)
        ctype = get_content_type(obj)
        permission = _ensure_permission(perm, ctype)

        kwargs = {"permission": permission, self.user_or_group_field: user_or_group}
        if self.is_generic():
            kwargs["content_type"] = ctype
            kwargs["object_pk"] = obj.pk
            if _is_using_default_content_type():
                kwargs["defaults"] = {"content_object": obj}
        else:
            kwargs["content_object"] = obj
        obj_perm, _ = self.get_or_create(**kwargs)
        return obj_perm

    def bulk_assign_perm(
        self, perm: _PermType, user_or_group: Any, queryset: Union[QuerySet, list], ignore_conflicts: bool = False
    ) -> list:
        """
        Bulk assigns permissions with given `perm` for an objects in `queryset` and
        `user_or_group`.
        """
        if isinstance(queryset, list):
            if not queryset:
                return []
            ctype = get_content_type(queryset[0])
        else:
            ctype = get_content_type(queryset.model)

        permission = _ensure_permission(perm, ctype)
        checker = ObjectPermissionChecker(user_or_group)
        checker.prefetch_perms(queryset)

        assigned_perms = []
        for instance in queryset:
            if not checker.has_perm(permission.codename, instance):
                kwargs = {"permission": permission, self.user_or_group_field: user_or_group}
                if self.is_generic():
                    kwargs["content_type"] = ctype
                    kwargs["object_pk"] = instance.pk
                else:
                    kwargs["content_object"] = instance
                assigned_perms.append(self.model(**kwargs))
        self.model.objects.bulk_create(assigned_perms, ignore_conflicts=ignore_conflicts)

        return assigned_perms

    def assign_perm_to_many(
        self, perm: _PermType, users_or_groups: Any, obj: Model, ignore_conflicts: bool = False
    ) -> list:
        """
        Bulk assigns given `perm` for the object `obj` to a set of users or a set of groups.
        """
        ctype = get_content_type(obj)
        permission = _ensure_permission(perm, ctype)

        kwargs = {"permission": permission}
        if self.is_generic():
            kwargs["content_type"] = ctype
            kwargs["object_pk"] = obj.pk
        else:
            kwargs["content_object"] = obj

        to_add = []
        field = self.user_or_group_field
        for user in users_or_groups:
            kwargs[field] = user
            to_add.append(self.model(**kwargs))

        return self.model.objects.bulk_create(to_add, ignore_conflicts=ignore_conflicts)

    def assign(self, perm: _PermType, user_or_group: Any, obj: Model) -> Any:
        """Depreciated function name left in for compatibility"""
        warnings.warn(
            "UserObjectPermissionManager method 'assign' is being renamed to 'assign_perm'. Update your code accordingly as old name will be depreciated in 2.0 version.",
            DeprecationWarning,
        )
        return self.assign_perm(perm, user_or_group, obj)

    def remove_perm(self, perm: _PermType, user_or_group: Any, obj: Model) -> tuple[int, dict]:
        """
        Removes permission `perm` for an instance `obj` and given `user_or_group`.

        Please note that we do NOT fetch object permission from database -
        we use `Queryset.delete` method for removing it.
        The main implication of this is that `post_delete` signals would NOT be fired.
        """
        if getattr(obj, "pk", None) is None:
            raise ObjectNotPersisted("Object %s needs to be persisted first" % obj)

        filters = Q(**{self.user_or_group_field: user_or_group})
        filters &= _get_perm_filter(perm, model=obj)
        if self.is_generic():
            filters &= Q(object_pk=obj.pk)
        else:
            filters &= Q(content_object__pk=obj.pk)
        return self.filter(filters).delete()

    def bulk_remove_perm(
        self, perm: _PermType, user_or_group: Any, queryset: Union[QuerySet, list]
    ) -> tuple[int, dict]:
        """
        Removes permission `perm` for a `queryset` and given `user_or_group`.

        Please note that we do NOT fetch object permission from database -
        we use `Queryset.delete` method for removing it.
        The main implication of this is that `post_delete` signals would NOT be fired.
        """
        filters = Q(**{self.user_or_group_field: user_or_group})

        if isinstance(queryset, list):
            if not queryset:
                return (0, {})
            ctype = get_content_type(queryset[0])
        else:
            ctype = get_content_type(queryset.model)

        filters &= _get_perm_filter(perm, ctype=ctype)
        if self.is_generic():
            if isinstance(queryset, list):
                filters &= Q(object_pk__in=[str(obj.pk) for obj in queryset])
            else:
                filters &= Q(object_pk__in=[str(pk) for pk in queryset.values_list("pk", flat=True)])
        else:
            filters &= Q(content_object__in=queryset)

        return self.filter(filters).delete()

    def remove_perm_from_many(self, perm: _PermType, users_or_groups: Any, obj: Model) -> tuple[int, dict]:
        """
        Bulk removes given `perm` for the object `obj` from a set of users or a set of groups.
        """
        ctype = get_content_type(obj)
        filters = _get_perm_filter(perm, ctype=ctype)
        if self.is_generic():
            filters &= Q(object_pk=str(obj.pk))
        else:
            filters &= Q(content_object=obj)

        if isinstance(users_or_groups, list):
            to_remove = [item.pk for item in users_or_groups]
        else:
            to_remove = users_or_groups.values_list("pk", flat=True)

        filters &= Q(**{f"{self.user_or_group_field}_id__in": to_remove})

        return self.filter(filters).delete()


class UserObjectPermissionManager(BaseObjectPermissionManager):
    """
    See Also:
        `guardian.managers.UserObjectPermissionManager`
    """

    pass


class GroupObjectPermissionManager(BaseObjectPermissionManager):
    """
    See Also:
        `guardian.managers.UserObjectPermissionManager`
    """

    pass
