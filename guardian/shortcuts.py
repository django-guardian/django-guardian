"""
Convenient shortcuts to manage or check object permissions.
"""
from django.contrib.auth.models import Permission, User, Group
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.shortcuts import _get_queryset
from guardian.core import ObjectPermissionChecker
from guardian.exceptions import MixedContentTypeError
from guardian.exceptions import WrongAppError
from guardian.models import UserObjectPermission, GroupObjectPermission
from guardian.utils import get_identity
from itertools import groupby

def assign(perm, user_or_group, obj=None):
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
    >>> from django.contrib.auth.models import User, Group
    >>> from guardian.shortcuts import assign
    >>> site = Site.objects.get_current()
    >>> user = User.objects.create(username='joe')
    >>> assign("change_site", user, site)
    <UserObjectPermission: example.com | joe | change_site>
    >>> user.has_perm("change_site", site)
    True

    ... or we can assign permission for group:

    >>> group = Group.objects.create(name='joe-group')
    >>> user.groups.add(group)
    >>> assign("delete_site", group, site)
    <GroupObjectPermission: example.com | joe-group | delete_site>
    >>> user.has_perm("delete_site", site)
    True

    **Global permissions**

    This function may also be used to assign standard, *global* permissions if
    ``obj`` parameter is omitted. Added Permission would be returned in that
    case:

    >>> assign("sites.change_site", user)
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
        return UserObjectPermission.objects.assign(perm, user, obj)
    if group:
        return GroupObjectPermission.objects.assign(perm, group, obj)

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
        UserObjectPermission.objects.remove_perm(perm, user, obj)
    if group:
        GroupObjectPermission.objects.remove_perm(perm, group, obj)

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
    if isinstance(cls, str):
        app_label, model_name = cls.split('.')
        model = models.get_model(app_label, model_name)
    else:
        model = cls
    ctype = ContentType.objects.get_for_model(model)
    return Permission.objects.filter(content_type=ctype)

def get_users_with_perms(obj, attach_perms=False):
    """
    Returns queryset of all ``User`` objects with *any* object permissions for
    the given ``obj``.

    :param obj: persisted Django's ``Model`` instance

    :param attach_perms: Default: ``False``. If set to ``True`` result would be
      dictionary of ``User`` instances with permissions' codenames list as
      values. This would fetch users eagerly!

    Example::

        >>> from django.contrib.auth.models import User
        >>> from django.contrib.flatpages.models import FlatPage
        >>> from guardian.shortcuts import assign, get_users_with_perms
        >>>
        >>> page = FlatPage.objects.create(title='Some page', path='/some/page/')
        >>> joe = User.objects.create_user('joe', 'joe@example.com', 'joesecret')
        >>> assign('change_flatpage', joe, page)
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
        qset = Q(
            userobjectpermission__content_type=ctype,
            userobjectpermission__object_pk=obj.pk)
        qset = qset | Q(
            groups__groupobjectpermission__content_type=ctype,
            groups__groupobjectpermission__object_pk=obj.pk,
        )
        return User.objects.filter(qset).distinct()
    else:
        # TODO: Do not hit db for each user!
        users = {}
        for user in get_users_with_perms(obj):
            users[user] = get_perms(user, obj)
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

        >>> from django.contrib.auth.models import Group
        >>> from django.contrib.flatpages.models import FlatPage
        >>> from guardian.shortcuts import assign, get_groups_with_perms
        >>>
        >>> page = FlatPage.objects.create(title='Some page', path='/some/page/')
        >>> admins = Group.objects.create(name='Admins')
        >>> assign('change_flatpage', group, page)
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
        groups = Group.objects\
            .filter(
                groupobjectpermission__content_type=ctype,
                groupobjectpermission__object_pk=obj.pk,
            )\
            .distinct()
        return groups
    else:
        # TODO: Do not hit db for each group!
        groups = {}
        for group in get_groups_with_perms(obj):
            if not group in groups:
                groups[group] = get_perms(group, obj)
        return groups

def get_objects_for_user(user, perms, klass=None):
    """
    Returns queryset of objects for which given ``user`` has *all*
    permissions from ``perms``.

    :param user: ``User`` instance for which objects would be returned
    :param perms: sequence with permissions as strings which should be checked.
      if ``klass`` parameter is not given, those should be full permission
      names rather than only codenames (i.e. ``auth.change_user``). If more than
      one permission is present within sequence, theirs content type **must** be
      the same or ``MixedContentTypeError`` exception would be raised. For
      convenience, may be given as single permission (string).
    :param klass: may be a Model, Manager or QuerySet object. If not given
      this parameter would be computed based on given ``params``.

    :raises MixedContentTypeError:
    :raises WrongAppError:

    Excample::

        >>> from guardian.shortcuts import get_objects_for_user
        >>> joe = User.objects.get(username='joe')
        >>> get_objects_for_user(joe, ['auth.change_group'])
        []
        >>> from guardian.shortcuts import assign
        >>> group = Group.objects.create('some group')
        >>> assign('auth.change_group', joe, group)
        >>> get_objects_for_user(joe, ['auth.change_group'])
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
    q1 = Q(
        permission__content_type=ctype,
        permission__codename__in=codenames,
    )
    q2 = Q(
        user__groups__groupobjectpermission__permission__content_type=ctype,
        user__groups__groupobjectpermission__permission__codename__in=codenames,
    )
    qset = q1 | q2
    rows = UserObjectPermission.objects\
        .filter(user=user)\
        .filter(qset)\
        .values_list('object_pk', 'permission__codename')
    keyfunc = lambda row: row[0] # sorting/grouping by pk (first in result tuple)
    rows = sorted(rows, key=keyfunc)
    pk_list = []
    for pk, group in groupby(rows, keyfunc):
        obj_codenames = set((e[1] for e in group))
        if codenames.issubset(obj_codenames):
            pk_list.append(pk)

    objects = queryset.filter(pk__in=pk_list)
    return objects

