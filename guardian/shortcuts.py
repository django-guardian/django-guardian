"""
Convenient shortcuts to manage or check object permissions.
"""
from __future__ import unicode_literals

from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.shortcuts import _get_queryset
from itertools import groupby

from guardian.compat import get_user_model
from guardian.compat import basestring
from guardian.core import ObjectPermissionChecker
from guardian.exceptions import MixedContentTypeError
from guardian.exceptions import WrongAppError
from guardian.utils import get_identity
from guardian.utils import get_user_obj_perms_model
from guardian.utils import get_group_obj_perms_model
import warnings

def assign_perm(perm, user_or_group, obj=None):
    """
    Assigns permission to user/group and object pair.

    :param perm: proper permission for given ``obj``, as string (in format:
      ``app_label.codename`` or ``codename``). If ``obj`` is not given, must
      be in format ``app_label.codename``.

    :param user_or_group: instance of ``User``, ``AnonymousUser`` or ``Group``;
      passing any other object would raise
      ``guardian.exceptions.NotUserNorGroup`` exception

    :param obj: persisted Django's ``Model`` instance or ``None`` if assigning
      global permission. Default is ``None``.

    We can assign permission for ``Model`` instance for specific user:

    >>> from django.contrib.sites.models import Site
    >>> from guardian.models import User, Group
    >>> from guardian.shortcuts import assign_perm
    >>> site = Site.objects.get_current()
    >>> user = User.objects.create(username='joe')
    >>> assign_perm("change_site", user, site)
    <UserObjectPermission: example.com | joe | change_site>
    >>> user.has_perm("change_site", site)
    True

    ... or we can assign permission for group:

    >>> group = Group.objects.create(name='joe-group')
    >>> user.groups.add(group)
    >>> assign_perm("delete_site", group, site)
    <GroupObjectPermission: example.com | joe-group | delete_site>
    >>> user.has_perm("delete_site", site)
    True

    **Global permissions**

    This function may also be used to assign standard, *global* permissions if
    ``obj`` parameter is omitted. Added Permission would be returned in that
    case:

    >>> assign_perm("sites.change_site", user)
    <Permission: sites | site | Can change site>

    """

    user, group = get_identity(user_or_group)
    # If obj is None we try to operate on global permissions
    if obj is None:
        try:
            app_label, codename = perm.split('.', 1)
        except ValueError:
            raise ValueError("For global permissions, first argument must be in"
                " format: 'app_label.codename' (is %r)" % perm)
        perm = Permission.objects.get(content_type__app_label=app_label,
            codename=codename)
        if user:
            user.user_permissions.add(perm)
            return perm
        if group:
            group.permissions.add(perm)
            return perm
    perm = perm.split('.')[-1]
    if user:
        model = get_user_obj_perms_model(obj)
        return model.objects.assign_perm(perm, user, obj)
    if group:
        model = get_group_obj_perms_model(obj)
        return model.objects.assign_perm(perm, group, obj)

def assign(perm, user_or_group, obj=None):
    """ Depreciated function name left in for compatibility"""
    warnings.warn("Shortcut function 'assign' is being renamed to 'assign_perm'. Update your code accordingly as old name will be depreciated in 1.0.5 version.", DeprecationWarning)
    return assign_perm(perm, user_or_group, obj)

def remove_perm(perm, user_or_group=None, obj=None):
    """
    Removes permission from user/group and object pair.

    :param perm: proper permission for given ``obj``, as string (in format:
      ``app_label.codename`` or ``codename``). If ``obj`` is not given, must
      be in format ``app_label.codename``.

    :param user_or_group: instance of ``User``, ``AnonymousUser`` or ``Group``;
      passing any other object would raise
      ``guardian.exceptions.NotUserNorGroup`` exception

    :param obj: persisted Django's ``Model`` instance or ``None`` if assigning
      global permission. Default is ``None``.

    """
    user, group = get_identity(user_or_group)
    if obj is None:
        try:
            app_label, codename = perm.split('.', 1)
        except ValueError:
            raise ValueError("For global permissions, first argument must be in"
                " format: 'app_label.codename' (is %r)" % perm)
        perm = Permission.objects.get(content_type__app_label=app_label,
            codename=codename)
        if user:
            user.user_permissions.remove(perm)
            return
        elif group:
            group.permissions.remove(perm)
            return
    perm = perm.split('.')[-1]
    if user:
        model = get_user_obj_perms_model(obj)
        model.objects.remove_perm(perm, user, obj)
    if group:
        model = get_group_obj_perms_model(obj)
        model.objects.remove_perm(perm, group, obj)

def get_perms(user_or_group, obj):
    """
    Returns permissions for given user/group and object pair, as list of
    strings.
    """
    check = ObjectPermissionChecker(user_or_group)
    return check.get_perms(obj)

def get_perms_for_model(cls):
    """
    Returns queryset of all Permission objects for the given class. It is
    possible to pass Model as class or instance.
    """
    if isinstance(cls, basestring):
        app_label, model_name = cls.split('.')
        model = models.get_model(app_label, model_name)
    else:
        model = cls
    ctype = ContentType.objects.get_for_model(model)
    return Permission.objects.filter(content_type=ctype)

def get_users_with_perms(obj, attach_perms=False, with_superusers=False,
        with_group_users=True):
    """
    Returns queryset of all ``User`` objects with *any* object permissions for
    the given ``obj``.

    :param obj: persisted Django's ``Model`` instance

    :param attach_perms: Default: ``False``. If set to ``True`` result would be
      dictionary of ``User`` instances with permissions' codenames list as
      values. This would fetch users eagerly!

    :param with_superusers: Default: ``False``. If set to ``True`` result would
      contain all superusers.

    :param with_group_users: Default: ``True``. If set to ``False`` result would
      **not** contain those users who have only group permissions for given
      ``obj``.

    Example::

        >>> from django.contrib.flatpages.models import FlatPage
        >>> from django.contrib.auth.models import User
        >>> from guardian.shortcuts import assign_perm, get_users_with_perms
        >>>
        >>> page = FlatPage.objects.create(title='Some page', path='/some/page/')
        >>> joe = User.objects.create_user('joe', 'joe@example.com', 'joesecret')
        >>> assign_perm('change_flatpage', joe, page)
        >>>
        >>> get_users_with_perms(page)
        [<User: joe>]
        >>>
        >>> get_users_with_perms(page, attach_perms=True)
        {<User: joe>: [u'change_flatpage']}

    """
    ctype = ContentType.objects.get_for_model(obj)
    if not attach_perms:
        # It's much easier without attached perms so we do it first if that is
        # the case
        user_model = get_user_obj_perms_model(obj)
        related_name = user_model.user.field.related_query_name()
        if user_model.objects.is_generic():
            user_filters = {
                '%s__content_type' % related_name: ctype,
                '%s__object_pk' % related_name: obj.pk,
            }
        else:
            user_filters = {'%s__content_object' % related_name: obj}
        qset = Q(**user_filters)
        if with_group_users:
            group_model = get_group_obj_perms_model(obj)
            group_rel_name = group_model.group.field.related_query_name()
            if group_model.objects.is_generic():
                group_filters = {
                    'groups__%s__content_type' % group_rel_name: ctype,
                    'groups__%s__object_pk' % group_rel_name: obj.pk,
                }
            else:
                group_filters = {
                    'groups__%s__content_object' % group_rel_name: obj,
                }
            qset = qset | Q(**group_filters)
        if with_superusers:
            qset = qset | Q(is_superuser=True)
        return get_user_model().objects.filter(qset).distinct()
    else:
        # TODO: Do not hit db for each user!
        users = {}
        for user in get_users_with_perms(obj,
                with_group_users=with_group_users):
            users[user] = sorted(get_perms(user, obj))
        return users

def get_groups_with_perms(obj, attach_perms=False):
    """
    Returns queryset of all ``Group`` objects with *any* object permissions for
    the given ``obj``.

    :param obj: persisted Django's ``Model`` instance

    :param attach_perms: Default: ``False``. If set to ``True`` result would be
      dictionary of ``Group`` instances with permissions' codenames list as
      values. This would fetch groups eagerly!

    Example::

        >>> from django.contrib.flatpages.models import FlatPage
        >>> from guardian.shortcuts import assign_perm, get_groups_with_perms
        >>> from guardian.models import Group
        >>>
        >>> page = FlatPage.objects.create(title='Some page', path='/some/page/')
        >>> admins = Group.objects.create(name='Admins')
        >>> assign_perm('change_flatpage', group, page)
        >>>
        >>> get_groups_with_perms(page)
        [<Group: admins>]
        >>>
        >>> get_groups_with_perms(page, attach_perms=True)
        {<Group: admins>: [u'change_flatpage']}

    """
    ctype = ContentType.objects.get_for_model(obj)
    if not attach_perms:
        # It's much easier without attached perms so we do it first if that is
        # the case
        group_model = get_group_obj_perms_model(obj)
        group_rel_name = group_model.group.field.related_query_name()
        if group_model.objects.is_generic():
            group_filters = {
                '%s__content_type' % group_rel_name: ctype,
                '%s__object_pk' % group_rel_name: obj.pk,
            }
        else:
            group_filters = {'%s__content_object' % group_rel_name: obj}
        groups = Group.objects.filter(**group_filters).distinct()
        return groups
    else:
        # TODO: Do not hit db for each group!
        groups = {}
        for group in get_groups_with_perms(obj):
            if not group in groups:
                groups[group] = sorted(get_perms(group, obj))
        return groups

def get_objects_for_user(user, perms, klass=None, use_groups=True, any_perm=False):
    """
    Returns queryset of objects for which a given ``user`` has *all*
    permissions present at ``perms``.

    :param user: ``User`` instance for which objects would be returned
    :param perms: single permission string, or sequence of permission strings
      which should be checked.
      If ``klass`` parameter is not given, those should be full permission
      names rather than only codenames (i.e. ``auth.change_user``). If more than
      one permission is present within sequence, their content type **must** be
      the same or ``MixedContentTypeError`` exception would be raised.
    :param klass: may be a Model, Manager or QuerySet object. If not given
      this parameter would be computed based on given ``params``.
    :param use_groups: if ``False``, wouldn't check user's groups object
      permissions. Default is ``True``.
    :param any_perm: if True, any of permission in sequence is accepted

    :raises MixedContentTypeError: when computed content type for ``perms``
      and/or ``klass`` clashes.
    :raises WrongAppError: if cannot compute app label for given ``perms``/
      ``klass``.

    Example::

        >>> from guardian.shortcuts import get_objects_for_user
        >>> joe = User.objects.get(username='joe')
        >>> get_objects_for_user(joe, 'auth.change_group')
        []
        >>> from guardian.shortcuts import assign_perm
        >>> group = Group.objects.create('some group')
        >>> assign_perm('auth.change_group', joe, group)
        >>> get_objects_for_user(joe, 'auth.change_group')
        [<Group some group>]

    The permission string can also be an iterable. Continuing with the previous example:

        >>> get_objects_for_user(joe, ['auth.change_group', 'auth.delete_group'])
        []
        >>> get_objects_for_user(joe, ['auth.change_group', 'auth.delete_group'], any_perm=True)
        [<Group some group>]
        >>> assign_perm('auth.delete_group', joe, group)
        >>> get_objects_for_user(joe, ['auth.change_group', 'auth.delete_group'])
        [<Group some group>]

    """
    if isinstance(perms, basestring):
        perms = [perms]
    ctype = None
    app_label = None
    codenames = set()

    # Compute codenames set and ctype if possible
    for perm in perms:
        if '.' in perm:
            new_app_label, codename = perm.split('.', 1)
            if app_label is not None and app_label != new_app_label:
                raise MixedContentTypeError("Given perms must have same app "
                    "label (%s != %s)" % (app_label, new_app_label))
            else:
                app_label = new_app_label
        else:
            codename = perm
        codenames.add(codename)
        if app_label is not None:
            new_ctype = ContentType.objects.get(app_label=app_label,
                permission__codename=codename)
            if ctype is not None and ctype != new_ctype:
                raise MixedContentTypeError("ContentType was once computed "
                    "to be %s and another one %s" % (ctype, new_ctype))
            else:
                ctype = new_ctype

    # Compute queryset and ctype if still missing
    if ctype is None and klass is None:
        raise WrongAppError("Cannot determine content type")
    elif ctype is None and klass is not None:
        queryset = _get_queryset(klass)
        ctype = ContentType.objects.get_for_model(queryset.model)
    elif ctype is not None and klass is None:
        queryset = _get_queryset(ctype.model_class())
    else:
        queryset = _get_queryset(klass)
        if ctype.model_class() != queryset.model:
            raise MixedContentTypeError("Content type for given perms and "
                "klass differs")

    # At this point, we should have both ctype and queryset and they should
    # match which means: ctype.model_class() == queryset.model
    # we should also have ``codenames`` list

    # First check if user is superuser and if so, return queryset immediately
    if user.is_superuser:
        return queryset

    # Now we should extract list of pk values for which we would filter queryset
    user_model = get_user_obj_perms_model(queryset.model)
    user_obj_perms_queryset = (user_model.objects
        .filter(user=user)
        .filter(permission__content_type=ctype)
        .filter(permission__codename__in=codenames))
    if user_model.objects.is_generic():
        fields = ['object_pk', 'permission__codename']
    else:
        fields = ['content_object__pk', 'permission__codename']
    user_obj_perms = user_obj_perms_queryset.values_list(*fields)
    data = list(user_obj_perms)
    if use_groups:
        group_model = get_group_obj_perms_model(queryset.model)
        group_filters = {
            'permission__content_type': ctype,
            'permission__codename__in': codenames,
            'group__%s' % get_user_model()._meta.module_name: user,
        }
        groups_obj_perms_queryset = group_model.objects.filter(**group_filters)
        if group_model.objects.is_generic():
            fields = ['object_pk', 'permission__codename']
        else:
            fields = ['content_object__pk', 'permission__codename']
        groups_obj_perms = groups_obj_perms_queryset.values_list(*fields)
        data += list(groups_obj_perms)
    keyfunc = lambda t: t[0] # sorting/grouping by pk (first in result tuple)
    data = sorted(data, key=keyfunc)
    pk_list = []
    for pk, group in groupby(data, keyfunc):
        obj_codenames = set((e[1] for e in group))
        if any_perm or codenames.issubset(obj_codenames):
            pk_list.append(pk)

    objects = queryset.filter(pk__in=pk_list)
    return objects

def get_objects_for_group(group, perms, klass=None, any_perm=False):
    """
    Returns queryset of objects for which a given ``group`` has *all*
    permissions present at ``perms``.

    :param group: ``Group`` instance for which objects would be returned.
    :param perms: single permission string, or sequence of permission strings
      which should be checked.
      If ``klass`` parameter is not given, those should be full permission
      names rather than only codenames (i.e. ``auth.change_user``). If more than
      one permission is present within sequence, their content type **must** be
      the same or ``MixedContentTypeError`` exception would be raised.
    :param klass: may be a Model, Manager or QuerySet object. If not given
      this parameter would be computed based on given ``params``.
    :param any_perm: if True, any of permission in sequence is accepted

    :raises MixedContentTypeError: when computed content type for ``perms``
      and/or ``klass`` clashes.
    :raises WrongAppError: if cannot compute app label for given ``perms``/
      ``klass``.

    Example:

    Let's assume we have a ``Task`` model belonging to the ``tasker`` app with
    the default add_task, change_task and delete_task permissions provided
    by Django::

        >>> from guardian.shortcuts import get_objects_for_group
        >>> from tasker import Task
        >>> group = Group.objects.create('some group')
        >>> task = Task.objects.create('some task')
        >>> get_objects_for_group(group, 'tasker.add_task')
        []
        >>> from guardian.shortcuts import assign_perm
        >>> assign_perm('tasker.add_task', group, task)
        >>> get_objects_for_group(group, 'tasker.add_task')
        [<Task some task>]

    The permission string can also be an iterable. Continuing with the previous example:
        >>> get_objects_for_group(group, ['tasker.add_task', 'tasker.delete_task'])
        []
        >>> assign_perm('tasker.delete_task', group, task)
        >>> get_objects_for_group(group, ['tasker.add_task', 'tasker.delete_task'])
        [<Task some task>]

    """
    if isinstance(perms, basestring):
        perms = [perms]
    ctype = None
    app_label = None
    codenames = set()

    # Compute codenames set and ctype if possible
    for perm in perms:
        if '.' in perm:
            new_app_label, codename = perm.split('.', 1)
            if app_label is not None and app_label != new_app_label:
                raise MixedContentTypeError("Given perms must have same app "
                    "label (%s != %s)" % (app_label, new_app_label))
            else:
                app_label = new_app_label
        else:
            codename = perm
        codenames.add(codename)
        if app_label is not None:
            new_ctype = ContentType.objects.get(app_label=app_label,
                permission__codename=codename)
            if ctype is not None and ctype != new_ctype:
                raise MixedContentTypeError("ContentType was once computed "
                    "to be %s and another one %s" % (ctype, new_ctype))
            else:
                ctype = new_ctype

    # Compute queryset and ctype if still missing
    if ctype is None and klass is None:
        raise WrongAppError("Cannot determine content type")
    elif ctype is None and klass is not None:
        queryset = _get_queryset(klass)
        ctype = ContentType.objects.get_for_model(queryset.model)
    elif ctype is not None and klass is None:
        queryset = _get_queryset(ctype.model_class())
    else:
        queryset = _get_queryset(klass)
        if ctype.model_class() != queryset.model:
            raise MixedContentTypeError("Content type for given perms and "
                "klass differs")

    # At this point, we should have both ctype and queryset and they should
    # match which means: ctype.model_class() == queryset.model
    # we should also have ``codenames`` list

    # Now we should extract list of pk values for which we would filter queryset
    group_model = get_group_obj_perms_model(queryset.model)
    groups_obj_perms_queryset = (group_model.objects
        .filter(group=group)
        .filter(permission__content_type=ctype)
        .filter(permission__codename__in=codenames))
    if group_model.objects.is_generic():
        fields = ['object_pk', 'permission__codename']
    else:
        fields = ['content_object__pk', 'permission__codename']
    groups_obj_perms = groups_obj_perms_queryset.values_list(*fields)
    data = list(groups_obj_perms)

    keyfunc = lambda t: t[0] # sorting/grouping by pk (first in result tuple)
    data = sorted(data, key=keyfunc)
    pk_list = []
    for pk, group in groupby(data, keyfunc):
        obj_codenames = set((e[1] for e in group))
        if any_perm or codenames.issubset(obj_codenames):
            pk_list.append(pk)

    objects = queryset.filter(pk__in=pk_list)
    return objects
