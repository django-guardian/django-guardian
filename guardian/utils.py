"""
django-guardian helper functions.

Functions defined within this module are a part of django-guardian’s internal functionality
and be considered unstable; their APIs may change in any future releases.
"""

import logging
import os
from itertools import chain
from typing import Union, Any, Optional

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Model, QuerySet
from django.http import (
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpRequest,
    HttpResponseRedirect,
    HttpResponse,
)
from django.shortcuts import render

from guardian.conf import settings as guardian_settings
from guardian.ctypes import get_content_type
from guardian.exceptions import NotUserNorGroup

logger = logging.getLogger(__name__)
abspath = lambda *p: os.path.abspath(os.path.join(*p))


def get_anonymous_user() -> Any:
    """Get the django-guardian equivalent of the anonymous user.

    It returns a `User` model instance (not `AnonymousUser`) depending on
    `ANONYMOUS_USER_NAME` configuration.

    See Also:
        See the configuration docs that explain that the Guardian anonymous user is
        not equivalent to Django’s AnonymousUser.

        - [Guardian Configuration](https://django-guardian.readthedocs.io/en/stable/configuration.html)
        - [ANONYMOUS_USER_NAME configuration](https://django-guardian.readthedocs.io/en/stable/configuration.html#anonymous-user-nam)
    """
    user_model = get_user_model()
    lookup = {user_model.USERNAME_FIELD: guardian_settings.ANONYMOUS_USER_NAME}  # type: ignore[attr-defined]
    return user_model.objects.get(**lookup)


def get_identity(identity: Model) -> tuple[Union[Any, None], Union[Any, None]]:
    """Get a tuple with the identity of the given input.

    Returns a tuple with one of the members set to `None` depending on whether the input is
    a `Group` instance or a `User` instance.
    Also accepts AnonymousUser instance but would return `User` instead.
    It is convenient and needed for authorization backend to support anonymous users.

    Returns:
         Either (user_obj, None) or (None, group_obj) depending on the input type.

    Parameters:
        identity (User | Group): Instance of `User` or `Group` to get identity from.

    Raises:
        NotUserNorGroup: If the function cannot return proper identity instance

    Examples:
        ```shell
        >>> from django.contrib.auth.models import User, Group
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
        ```
    """
    if isinstance(identity, AnonymousUser):
        identity = get_anonymous_user()

    group_model = get_group_obj_perms_model().group.field.related_model  # type: ignore[attr-defined]

    # get identity from queryset model type
    if isinstance(identity, QuerySet):
        identity_model_type = identity.model
        if identity_model_type == get_user_model():
            return identity, None
        elif identity_model_type == group_model:
            return None, identity

    # get identity from the first element in the list
    if isinstance(identity, list) and isinstance(identity[0], get_user_model()):
        return identity, None
    if isinstance(identity, list) and isinstance(identity[0], group_model):
        return None, identity

    if isinstance(identity, get_user_model()):
        return identity, None
    if isinstance(identity, group_model):
        return None, identity

    raise NotUserNorGroup("User/AnonymousUser or Group instance is required "
                          "(got %s)" % identity)



def get_40x_or_None(
    request: HttpRequest,
    perms: list[str],
    obj: Optional[Any] = None,
    login_url: Optional[Any] = None,
    redirect_field_name: Optional[str] = None,
    return_403: bool = False,
    return_404: bool = False,
    permission_denied_message: str = "",
    accept_global_perms: bool = False,
    any_perm: bool = False,
) -> Union[
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseRedirect,
    HttpResponse,
    None,
]:
    login_url = login_url or settings.LOGIN_URL
    redirect_field_name = redirect_field_name or REDIRECT_FIELD_NAME

    # Handles both original and with object provided permission check
    # as `obj` defaults to None

    has_permissions = False
    # global perms check first (if accept_global_perms)
    if accept_global_perms:
        has_permissions = all(request.user.has_perm(perm) for perm in perms)  # type: ignore[union-attr]
    # if still no permission granted, try obj perms
    if not has_permissions:
        if any_perm:
            has_permissions = any(request.user.has_perm(perm, obj) for perm in perms)  # type: ignore[union-attr]
        else:
            has_permissions = all(request.user.has_perm(perm, obj) for perm in perms)  # type: ignore[union-attr]

    if not has_permissions:
        if return_403:
            if guardian_settings.RENDER_403:
                response = render(
                    request,
                    guardian_settings.TEMPLATE_403,
                    context={"exception": permission_denied_message},
                )
                response.status_code = 403
                return response
            elif guardian_settings.RAISE_403:
                raise PermissionDenied(permission_denied_message)
            return HttpResponseForbidden()
        if return_404:
            if guardian_settings.RENDER_404:
                response = render(request, guardian_settings.TEMPLATE_404)
                response.status_code = 404
                return response
            elif guardian_settings.RAISE_404:
                raise ObjectDoesNotExist
            return HttpResponseNotFound()
        else:
            from django.contrib.auth.views import redirect_to_login

            return redirect_to_login(
                request.get_full_path(), login_url, redirect_field_name
            )
    return None


from django.apps import apps as django_apps
from django.core.exceptions import ImproperlyConfigured


def get_obj_perm_model_by_conf(setting_name: str) -> type[Model]:
    """Return the model that matches the guardian settings.

    Parameters:
        setting_name (str): The name of the setting to get the model from.

    Returns:
        The model class that matches the guardian settings.

    Raises:
        ImproperlyConfigured: If the setting value is not an installed model or
            does not follow the format 'app_label.model_name'.
    """
    setting_value: str = getattr(guardian_settings, setting_name)
    try:
        return django_apps.get_model(setting_value, require_ready=False)  # type: ignore
    except ValueError as e:
        raise ImproperlyConfigured("{} must be of the form 'app_label.model_name'".format(setting_value)) from e
    except LookupError as e:
        raise ImproperlyConfigured(
            "{} refers to model '{}' that has not been installed".format(setting_name, setting_value)
        ) from e


def clean_orphan_obj_perms() -> int:
    """Seeks and removes all object permissions entries pointing at non-existing targets.

    Returns:
         The number of objects removed.
    """
    UserObjectPermission = get_user_obj_perms_model()
    GroupObjectPermission = get_group_obj_perms_model()

    deleted = 0
    # TODO: optimise
    for perm in chain(
        UserObjectPermission.objects.all().iterator(),
        GroupObjectPermission.objects.all().iterator(),
    ):
        if perm.content_object is None:
            logger.debug("Removing %s (pk=%d)" % (perm, perm.pk))
            perm.delete()
            deleted += 1
    logger.info("Total removed orphan object permissions instances: %d" %
                deleted)
    return deleted


# TODO: should raise error when multiple UserObjectPermission direct relations
# are defined

def get_obj_perms_model(obj: Optional[Model], base_cls: type[Model], generic_cls: type[Model]) -> type[Model]:
    """Return the matching object permission model for the obj class.

    Defaults to returning the generic object permission when no direct foreignkey is defined, or obj is None.
    """
    # Default to the generic object permission model
    # when None obj is provided
    if obj is None:
        return generic_cls

    if isinstance(obj, Model):
        obj = obj.__class__


    fields = (f for f in obj._meta.get_fields()  # type: ignore[union-attr] # obj is already checked for None
              if (f.one_to_many or f.one_to_one) and f.auto_created)

    for attr in fields:
        model = getattr(attr, "related_model", None)
        if (
            model
            and issubclass(model, base_cls)
            and model is not generic_cls
            and getattr(model, "enabled", True)
        ):
            # if model is generic one it would be returned anyway
            if not model.objects.is_generic():
                # make sure that content_object's content_type is the same as
                # the one of given obj
                fk = model._meta.get_field("content_object")
                if get_content_type(obj) == get_content_type(fk.remote_field.model):
                    return model
    return generic_cls


def get_user_obj_perms_model(obj: Optional[Model] = None) -> type[Model]:
    """Returns model class that connects given `obj` and User class.

    If obj is not specified, then the user generic object permission model
    that is returned is determined by the guardian settings for 'USER_OBJ_PERMS_MODEL'.
    """
    from guardian.models import UserObjectPermissionBase
    UserObjectPermission = get_obj_perm_model_by_conf("USER_OBJ_PERMS_MODEL")
    return get_obj_perms_model(obj, UserObjectPermissionBase, UserObjectPermission)


def get_group_obj_perms_model(obj: Optional[Model] = None) -> type[Model]:
    """Returns model class that connects given `obj` and Group class.

    If obj is not specified, then the group generic object permission model
    that is returned is determined by the guardian settings for 'GROUP_OBJ_PERMS_MODEL'.
    """
    from guardian.models import GroupObjectPermissionBase
    GroupObjectPermission = get_obj_perm_model_by_conf("GROUP_OBJ_PERMS_MODEL")
    return get_obj_perms_model(obj, GroupObjectPermissionBase, GroupObjectPermission)


def evict_obj_perms_cache(obj: Any) -> bool:
    if hasattr(obj, "_guardian_perms_cache"):
        delattr(obj, "_guardian_perms_cache")
        return True
    return False
