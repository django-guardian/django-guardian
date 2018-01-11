from __future__ import unicode_literals
from django.contrib.auth.models import Permission
from django.db.models.query import QuerySet
from django.utils.encoding import force_text
from guardian.compat import get_user_model
from guardian.conf.settings import effective_fallback
from guardian.ctypes import get_content_type
from guardian.utils import get_group_obj_perms_model, get_identity, get_user_obj_perms_model
from itertools import chain


def _get_pks_model_and_ctype(objects):
    """
    Returns the primary keys, model and content type of an iterable of Django model objects.
    Assumes that all objects are of the same content type.
    """

    if isinstance(objects, QuerySet):
        model = objects.model
        pks = [force_text(pk) for pk in objects.values_list('pk', flat=True)]
        ctype = get_content_type(model)
    else:
        pks = []
        for idx, obj in enumerate(objects):
            if not idx:
                model = type(obj)
                ctype = get_content_type(model)
            pks.append(force_text(obj.pk))

    return pks, model, ctype


class ObjectPermissionChecker(object):
    """
    Generic object permissions checker class being the heart of
    ``django-guardian``.

    .. note::
       Once checked for single object, permissions are stored and we don't hit
       database again if another check is called for this object. This is great
       for templates, views or other request based checks (assuming we don't
       have hundreds of permissions on a single object as we fetch all
       permissions for checked object).

       On the other hand, if we call ``has_perm`` for perm1/object1, then we
       change permission state and call ``has_perm`` again for same
       perm1/object1 on same instance of ObjectPermissionChecker we won't see a
       difference as permissions are already fetched and stored within cache
       dictionary.
    """

    def __init__(self, user_or_group=None):
        """
        Constructor for ObjectPermissionChecker.

        :param user_or_group: should be an ``User``, ``AnonymousUser`` or
          ``Group`` instance
        """
        self.user, self.group = get_identity(user_or_group)
        self._obj_perms_cache = {}

    def has_perm(self, perm, obj, fallback_to_model=None):
        """
        Checks if user/group has given permission for object.

        :param perm: permission as string, may or may not contain app_label
          prefix (if not prefixed, we grab app_label from ``obj``)
        :param obj: Django model instance for which permission should be checked

        """
        if self.user and not self.user.is_active:
            return False
        elif self.user and self.user.is_superuser:
            return True
        perm = perm.split('.')[-1]
        return perm in self.get_perms(obj, fallback_to_model=None)

    def get_group_filters(self, obj):
        User = get_user_model()
        ctype = get_content_type(obj)

        group_model = get_group_obj_perms_model(obj)
        group_rel_name = group_model.permission.field.related_query_name()
        if self.user:
            fieldname = '%s__group__%s' % (
                group_rel_name,
                User.groups.field.related_query_name(),
            )
            group_filters = {fieldname: self.user}
        else:
            group_filters = {'%s__group' % group_rel_name: self.group}

        if group_model.objects.is_generic():
            group_filters.update({
                '%s__content_type' % group_rel_name: ctype,
                '%s__object_pk' % group_rel_name: obj.pk,
            })
        else:
            group_filters['%s__content_object' % group_rel_name] = obj

        return group_filters


    def get_user_filters(self, obj):
        ctype = get_content_type(obj)
        perms_model = get_user_obj_perms_model(obj) # ex. UserObjectPermission
        related_name = perms_model.permission.field.related_query_name() # ex. userobjectpermission

        user_filters = {'%s__user' % related_name: self.user}
        if perms_model.objects.is_generic():
            user_filters.update({
                '%s__content_type' % related_name: ctype,
                '%s__object_pk' % related_name: obj.pk,
            })
        else:
            user_filters['%s__content_object' % related_name] = obj

        return user_filters

    def get_user_perms(self, obj, fallback_to_model=None):
        ctype = get_content_type(obj)

        obj_perms = Permission.objects.filter(content_type=ctype) \
                .filter(**self.get_user_filters(obj)) \
                .values_list("codename", flat=True)

        # add missing from user's model level perms
        if effective_fallback(fallback_to_model):
            return set(list(obj_perms)) \
                .union(set(list(self.get_user_model_perms(obj))))

        return obj_perms

    def get_user_model_perms(self, obj):
        """
        self.user's model level permissions for the obj's content type
        hits db
        """
        ctype = get_content_type(obj)
        return self.user.user_permissions.filter(content_type=ctype) \
            .values_list("codename", flat=True)

    def get_group_perms(self, obj, fallback_to_model=None):
        ctype = get_content_type(obj)

        obj_perms = Permission.objects.filter(content_type=ctype) \
                .filter(**self.get_group_filters(obj)) \
                .values_list("codename", flat=True)

        # add missing from user's groups' model level perms
        if effective_fallback(fallback_to_model):
            if self.user:
                return set(list(obj_perms))\
                    .union(set(list(self.get_user_groups_model_perms(obj))))
            # self.group
            return set(list(obj_perms))\
                .union(set(list(self.get_group_model_perms(obj))))

        return obj_perms

    def get_user_groups_model_perms(self, obj):
        """
        self.user's groups' model level permissions for the obj's content type
        hits db
        """
        ctype = get_content_type(obj)
        user_groups_field = self.user._meta.get_field('groups')
        user_groups_query = 'group__%s' % user_groups_field.related_query_name()
        return Permission.objects \
            .filter(content_type=ctype, **{user_groups_query: self.user}) \
            .values_list("codename", flat=True)

    def get_group_model_perms(self, obj):
        """
        self.group's model level permissions for the obj's content type
        hits db
        """
        ctype = get_content_type(obj)
        return self.group.permissions.filter(content_type=ctype) \
            .values_list("codename", flat=True)

    def get_perms(self, obj, fallback_to_model=None):
        """
        Returns list of ``codename``'s of all permissions for given ``obj``.

        :param obj: Django model instance for which permission should be checked

        """
        if self.user and not self.user.is_active:
            return []
        ctype = get_content_type(obj)
        key = self.get_local_cache_key(obj)
        if key not in self._obj_perms_cache:
            if self.user and self.user.is_superuser:
                perms = list(Permission.objects
                           .filter(content_type=ctype)
                           .values_list("codename", flat=True))
            elif self.user:
                # Query user and group permissions separately and then combine
                # the results to avoid a slow query
                user_perms = self.get_user_perms(obj, fallback_to_model)
                group_perms = self.get_group_perms(obj, fallback_to_model)
                perms = list(set(chain(user_perms, group_perms)))
            else:
                group_filters = self.get_group_filters(obj)
                perms = set(Permission.objects
                               .filter(content_type=ctype)
                               .filter(**group_filters)
                               .values_list("codename", flat=True))
                if effective_fallback(fallback_to_model):
                    perms = perms.union(set(self.get_group_model_perms(obj)))
                perms=list(perms)
            self._obj_perms_cache[key] = perms
            return perms
        return self._obj_perms_cache[key]

    def get_local_cache_key(self, obj):
        """
        Returns cache key for ``_obj_perms_cache`` dict.
        """
        ctype = get_content_type(obj)
        return (ctype.id, force_text(obj.pk))

    def prefetch_perms(self, objects):
        """
        Prefetches the permissions for objects in ``objects`` and puts them in the cache.

        :param objects: Iterable of Django model objects

        """
        if self.user and not self.user.is_active:
            return []

        User = get_user_model()
        pks, model, ctype = _get_pks_model_and_ctype(objects)

        if self.user and self.user.is_superuser:
            perms = list(chain(
                *Permission.objects
                .filter(content_type=ctype)
                .values_list("codename")))

            for pk in pks:
                key = (ctype.id, force_text(pk))
                self._obj_perms_cache[key] = perms

            return True

        group_model = get_group_obj_perms_model(model)

        if self.user:
            fieldname = 'group__%s' % (
                User.groups.field.related_query_name(),
            )
            group_filters = {fieldname: self.user}
        else:
            group_filters = {'group': self.group}

        if group_model.objects.is_generic():
            group_filters.update({
                'content_type': ctype,
                'object_pk__in': pks,
            })
        else:
            group_filters.update({
                'content_object_id__in': pks
            })

        if self.user:
            model = get_user_obj_perms_model(model)
            user_filters = {
                'user': self.user,
            }

            if model.objects.is_generic():
                user_filters.update({
                    'content_type': ctype,
                    'object_pk__in': pks
                })
            else:
                user_filters.update({
                    'content_object_id__in': pks
                })

            # Query user and group permissions separately and then combine
            # the results to avoid a slow query
            user_perms_qs = model.objects.filter(**user_filters).select_related('permission')
            group_perms_qs = group_model.objects.filter(**group_filters).select_related('permission')
            perms = chain(user_perms_qs, group_perms_qs)
        else:
            perms = chain(
                *(group_model.objects.filter(**group_filters).select_related('permission'),)
            )

        # initialize entry in '_obj_perms_cache' for all prefetched objects
        for obj in objects:
            key = self.get_local_cache_key(obj)
            if key not in self._obj_perms_cache:
                self._obj_perms_cache[key] = []

        for perm in perms:
            if type(perm).objects.is_generic():
                key = (ctype.id, perm.object_pk)
            else:
                key = (ctype.id, force_text(perm.content_object_id))

            self._obj_perms_cache[key].append(perm.permission.codename)

        return True
