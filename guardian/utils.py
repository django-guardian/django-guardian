"""
django-guardian helper functions.

Functions defined within this module should be considered as django-guardian's
internal functionality. They are **not** guaranteed to be stable - which means
they actual input parameters/output type may change in future releases.
"""
from __future__ import unicode_literals
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.models import AnonymousUser, Group
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Model
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from guardian.compat import get_user_model, get_remote_model, get_related_model, \
    get_model_fields
from guardian.conf import settings as guardian_settings
from guardian.ctypes import get_content_type
from guardian.exceptions import NotUserNorGroup
from itertools import chain

import django
import logging
import os

logger = logging.getLogger(__name__)
abspath = lambda *p: os.path.abspath(os.path.join(*p))


def get_anonymous_user():
    """
    Returns ``User`` instance (not ``AnonymousUser``) depending on
    ``ANONYMOUS_USER_NAME`` configuration.
    """
    User = get_user_model()
    lookup = {User.USERNAME_FIELD: guardian_settings.ANONYMOUS_USER_NAME}
    return User.objects.get(**lookup)


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


def get_40x_or_None(request, perms, obj=None, login_url=None,
                    redirect_field_name=None, return_403=False,
                    return_404=False, accept_global_perms=False):
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
        has_permissions = all(request.user.has_perm(perm, obj)
                              for perm in perms)

    if not has_permissions:
        if return_403:
            if guardian_settings.RENDER_403:
                if django.VERSION >= (1, 10):
                    response = render(request, guardian_settings.TEMPLATE_403)
                else:
                    response = render_to_response(
                        guardian_settings.TEMPLATE_403, {},
                        RequestContext(request))
                response.status_code = 403
                return response
            elif guardian_settings.RAISE_403:
                raise PermissionDenied
            return HttpResponseForbidden()
        if return_404:
            if guardian_settings.RENDER_404:
                if django.VERSION >= (1, 10):
                    response = render(request, guardian_settings.TEMPLATE_404)
                else:
                    response = render_to_response(
                        guardian_settings.TEMPLATE_404, {},
                        RequestContext(request))
                response.status_code = 404
                return response
            elif guardian_settings.RAISE_404:
                raise ObjectDoesNotExist
            return HttpResponseNotFound()
        else:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path(),
                                     login_url,
                                     redirect_field_name)


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
    for perm in chain(UserObjectPermission.objects.all().iterator(),
                      GroupObjectPermission.objects.all().iterator()):
        if perm.content_object is None:
            logger.debug("Removing %s (pk=%d)" % (perm, perm.pk))
            perm.delete()
            deleted += 1
    logger.info("Total removed orphan object permissions instances: %d" %
                deleted)
    return deleted


# TODO: should raise error when multiple UserObjectPermission direct relations
# are defined

def get_obj_perms_model(obj, base_model, generic_model):
    """
    returns ObjectPermission model associated with the obj

    this is, in the generic case, UserObjectPermission or GroupObjectPermission;

    or, if direct foreign keys used, a subclass of UserObjectPermissionBase,
        GroupObjectPermissionBase. Example: ProjectUserObjectPermission
        in other words: obj's model is properly FK'ed by an ObjectPermission
        model/table dedicated to it.

    :param obj:
    :param base_model:
    :param generic_model:
    :return:
    """

    if isinstance(obj, Model):
        obj_model = obj.__class__
    elif issubclass(obj, Model):
        obj_model = obj
    else:
        raise ValueError('obj must be either a Model or an instance of it')

    ctype = get_content_type(obj_model)
    model_fields = get_model_fields(obj_model)

    for field in model_fields:
        related_model = get_related_model(field)

        if (related_model and issubclass(related_model, base_model)
                and related_model is not generic_model
                # if field_model is generic, it would be returned anyway
                and not related_model.objects.is_generic()):
            content_obj_field = related_model._meta.get_field('content_object')
            # make sure that content_object's content_type is same as
            # the one of given obj
            if ctype == get_content_type(get_remote_model(content_obj_field)):
                return related_model
    return generic_model


def get_user_obj_perms_model(obj):
    """
    Returns the model that connects given ``obj`` and User model.
    Usually UserObjectPermission
    """
    from guardian.models import UserObjectPermissionBase
    from guardian.models import UserObjectPermission
    return get_obj_perms_model(obj, UserObjectPermissionBase, UserObjectPermission)


def get_group_obj_perms_model(obj):
    """
    Returns the model that connects given ``obj`` and Group model.
    Usually GroupObjectPermission
    """
    from guardian.models import GroupObjectPermissionBase
    from guardian.models import GroupObjectPermission
    return get_obj_perms_model(obj, GroupObjectPermissionBase, GroupObjectPermission)
