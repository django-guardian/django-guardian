"""
django-guardian helper functions.

Functions defined within this module should be considered as django-guardian's
internal functionality. They are **not** guaranteed to be stable - which means
they actual input parameters/output type may change in future releases.
"""
from __future__ import unicode_literals
import os
import logging
from itertools import chain
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.models import AnonymousUser, Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db.models import Model
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext, TemplateDoesNotExist
from django.utils.http import urlquote

from guardian.compat import get_user_model
from guardian.conf import settings as guardian_settings
from guardian.exceptions import NotUserNorGroup


logger = logging.getLogger(__name__)
abspath = lambda *p: os.path.abspath(os.path.join(*p))


def get_anonymous_user():
    """
    Returns ``User`` instance (not ``AnonymousUser``) depending on
    ``ANONYMOUS_USER_ID`` configuration.
    """
    return get_user_model().objects.get(id=guardian_settings.ANONYMOUS_USER_ID)


def get_identity(identity):
    """
    Returns (user_obj, None) or (None, group_obj) tuple depending on what is
    given. Also accepts AnonymousUser instance but would return ``User``
    instead - it is convenient and needed for authorization backend to support
    anonymous users.

    :param identity: either ``User`` or ``Group`` instance

    :raises ``NotUserNorGroup``: if cannot return proper identity instance

    **Examples**::

       >>> from django.contrib.auth.models import User
       >>> user = User.objects.create(username='joe')
       >>> get_identity(user)
       (<User: joe>, None)

       >>> group = Group.objects.create(name='users')
       >>> get_identity(group)
       (None, <Group: users>)

       >>> anon = AnonymousUser()
       >>> get_identity(anon)
       (<User: AnonymousUser>, None)

       >>> get_identity("not instance")
       ...
       NotUserNorGroup: User/AnonymousUser or Group instance is required (got )

    """
    if isinstance(identity, AnonymousUser):
        identity = get_anonymous_user()

    if isinstance(identity, get_user_model()):
        return identity, None
    elif isinstance(identity, Group):
        return None, identity

    raise NotUserNorGroup("User/AnonymousUser or Group instance is required "
        "(got %s)" % identity)


def get_403_or_None(request, perms, obj=None, login_url=None,
    redirect_field_name=None, return_403=False, accept_global_perms=False):
    login_url = login_url or settings.LOGIN_URL
    redirect_field_name = redirect_field_name or REDIRECT_FIELD_NAME

    # Handles both original and with object provided permission check
    # as ``obj`` defaults to None

    has_permissions = False
    # global perms check first (if accept_global_perms)
    if accept_global_perms:
        has_permissions = all(request.user.has_perm(perm) for perm in perms)
    # if still no permission granted, try obj perms
    if not has_permissions:
        has_permissions = all(request.user.has_perm(perm, obj) for perm in perms)

    if not has_permissions:
        if return_403:
            if guardian_settings.RENDER_403:
                try:
                    response = render_to_response(
                        guardian_settings.TEMPLATE_403, {},
                        RequestContext(request))
                    response.status_code = 403
                    return response
                except TemplateDoesNotExist as e:
                    if settings.DEBUG:
                        raise e
            elif guardian_settings.RAISE_403:
                raise PermissionDenied
            return HttpResponseForbidden()
        else:
            path = urlquote(request.get_full_path())
            tup = login_url, redirect_field_name, path
            return HttpResponseRedirect("%s?%s=%s" % tup)


def clean_orphan_obj_perms():
    """
    Seeks and removes all object permissions entries pointing at non-existing
    targets.

    Returns number of removed objects.
    """
    from guardian.models import UserObjectPermission
    from guardian.models import GroupObjectPermission


    deleted = 0
    # TODO: optimise
    for perm in chain(UserObjectPermission.objects.all(),
        GroupObjectPermission.objects.all()):
        if perm.content_object is None:
            logger.debug("Removing %s (pk=%d)" % (perm, perm.pk))
            perm.delete()
            deleted += 1
    logger.info("Total removed orphan object permissions instances: %d" %
        deleted)
    return deleted


# TODO: should raise error when multiple UserObjectPermission direct relations
# are defined

def get_obj_perms_model(obj, base_cls, generic_cls):
    if isinstance(obj, Model):
        obj = obj.__class__
    ctype = ContentType.objects.get_for_model(obj)
    for attr in obj._meta.get_all_related_objects():
        model = getattr(attr, 'model', None)
        if (model and issubclass(model, base_cls) and
                model is not generic_cls):
            # if model is generic one it would be returned anyway
            if not model.objects.is_generic():
                # make sure that content_object's content_type is same as
                # the one of given obj
                fk = model._meta.get_field_by_name('content_object')[0]
                if ctype == ContentType.objects.get_for_model(fk.rel.to):
                    return model
    return generic_cls


def get_user_obj_perms_model(obj):
    """
    Returns model class that connects given ``obj`` and User class.
    """
    from guardian.models import UserObjectPermissionBase
    from guardian.models import UserObjectPermission
    return get_obj_perms_model(obj, UserObjectPermissionBase, UserObjectPermission)


def get_group_obj_perms_model(obj):
    """
    Returns model class that connects given ``obj`` and Group class.
    """
    from guardian.models import GroupObjectPermissionBase
    from guardian.models import GroupObjectPermission
    return get_obj_perms_model(obj, GroupObjectPermissionBase, GroupObjectPermission)
