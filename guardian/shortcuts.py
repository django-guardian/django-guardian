"""
Convenient shortcuts to manage or check object permissions.
"""
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType

from guardian.core import ObjectPermissionChecker
from guardian.models import UserObjectPermission, GroupObjectPermission
from guardian.utils import get_identity

def assign(perm, user_or_group, obj):
    """
    Assigns permission to user/group and object pair.

    :param perm: proper permission for given ``obj``, as string (*codename*)

    :param user_or_group: instance of ``User``, ``AnonymousUser`` or ``Group``;
      passing any other object would raise
      ``guardian.exceptions.NotUserNorGroup`` exception

    :param obj: persisted Django's ``Model`` instance

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

    """

    perm = perm.split('.')[-1]
    user, group = get_identity(user_or_group)
    if user:
        return UserObjectPermission.objects.assign(perm, user, obj)
    if group:
        return GroupObjectPermission.objects.assign(perm, group, obj)

def remove_perm(perm, user_or_group=None, obj=None):
    """
    Removes permission from user/group and object pair.
    """
    perm = perm.split('.')[-1]
    user, group = get_identity(user_or_group)
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
    Returns queryset of all User objects with *any* object permissions for the
    given ``obj``.

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
        return User.objects.filter(qset)
    else:
        # TODO: Do not hit db for each user!
        users = {}
        for user in get_users_with_perms(obj):
            users[user] = get_perms(user, obj)
        return users

