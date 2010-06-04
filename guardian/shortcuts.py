"""
Convenient shortcuts to manage or check object permissions.
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission

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

