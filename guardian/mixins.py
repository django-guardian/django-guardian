from collections.abc import Iterable
from inspect import isawaitable
import sys
from types import GeneratorType
from typing import Any
import warnings

# Import deprecated decorator with fallback for Python < 3.13
if sys.version_info >= (3, 13):
    from warnings import deprecated
else:
    from typing_extensions import deprecated

from asgiref.sync import sync_to_async

try:
    from asgiref.sync import iscoroutinefunction
except ImportError:
    # asgiref < 3.6, which Django < 4.2 still allows. The asynchronous path is
    # disabled on those versions anyway, so the stricter detector is enough.
    from inspect import iscoroutinefunction

from django import VERSION as DJANGO_VERSION
from django.conf import settings
from django.contrib.auth.decorators import REDIRECT_FIELD_NAME, login_required
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db.models import Model, QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden, HttpResponseNotFound, HttpResponseRedirect

from guardian.shortcuts import get_objects_for_user
from guardian.utils import get_40x_or_None, get_anonymous_user, get_group_obj_perms_model, get_user_obj_perms_model

# Django 4.1.2 made the response for a disallowed HTTP method awaitable, which
# asynchronous views rely on. 4.1 is end of life, so 4.2 is the floor here.
# Two components only: comparing django.VERSION with three is deprecated.
_ASYNC_VIEWS_SUPPORTED = DJANGO_VERSION >= (4, 2)


class LoginRequiredMixin:
    """A login required mixin for use with class-based views.

    This Class is a light wrapper around the Django `login_required` decorator,
    function parameters are instead attributes defined on the class.

    Due to Python Method Resolution Order (MRO), this mixin must be added as the left
    most mixin of a view.

    Attributes:
        redirect_field_name (str): *Default*: `'next'`
        login_url (str): *Default*: `settings.LOGIN_URL`

    Example:
        ```python
        from guardian.mixins import LoginRequiredMixin
        from django.views.generic import View

        class SecretView(LoginRequiredMixin, View):
            redirect_field_name = 'foobar'
            login_url = '/let-me-in/'

            def get(self, request):
                return HttpResponse('secret-view')
        ```

    Note:
        The mixin has exactly the same flow as `login_required` decorator:

        - If the user isn't logged in, redirect to `settings.LOGIN_URL`, passing
        the current absolute path in the query string.
            - Example: `/accounts/login/?next=/polls/3/`.

        - If the user is logged in, execute the view normally.
        The view code is free to assume the user is logged in.


    See Also:
        - [Python MRO historical reference](https://docs.python.org/3/howto/mro.html)
    """

    redirect_field_name = REDIRECT_FIELD_NAME
    login_url = settings.LOGIN_URL

    def dispatch(self, request, *args, **kwargs):
        return login_required(redirect_field_name=self.redirect_field_name, login_url=self.login_url)(super().dispatch)(
            request, *args, **kwargs
        )


class PermissionRequiredMixin:
    """A view mixin that verifies if the current logged-in user has the specified permission.

    This mixin works by wrapping the `request.user.has_perm(...)` method.
    If a `get_object()` method is defined either manually or by including
    another mixin (e.g., `SingleObjectMixin`) or `self.object` is
    defined, then the permission will be tested against that specific instance.
    Alternatively, you can specify `get_permission_object()` method if `self.object`
    or `get_object()` does not return the object against you want to test permission

    The mixin does the following:

    - If the user isn't logged in, redirect to settings.LOGIN_URL, passing
    the current absolute path in the query string.
        - Example: /accounts/login/?next=/polls/3/.

    - If `raise_exception` is set to `True` a `PermissionDenied` (403) is raised
    instead of redirecting the user to `settings.LOGIN_URL`.

    - If the user is logged in, and passes the permission check, the view is executed normally.

    Note:
       Testing of a permission against a specific object instance requires an
       authentication backend that supports.
       The `guardian.backends.ObjectPermissionBackend` or a custom implementation
       must be listed under the list of authentication backends in your project.

    Attributes:
        permission_required (str | list[str]): permissions to check
            in form `"<app_label>.<permission codename>"`.
            Default is `None`.
        login_url (str): Default: `settings.LOGIN_URL`
        redirect_field_name (str): Default is `'next'`
        return_403 (bool): Returns 403 error page instead of redirecting.
            Default is `False`.
        return_404 (bool): Returns 404 error page instead of redirecting.
            Default is `False`.
        raise_exception (bool): Default is `False`
        permission_denied_message (str): A string to pass to the `PermissionDenied` exception.
            It is available in the 403 template context object as `exception`.
            Default is `''`.
        accept_global_perms (bool): Whether the mixin should first check for global perms.
            If none are found, proceed to check object level permissions.
            Default is `False`.
        permission_object (None | object): Object against which test the permission;
            if not set fallback to `self.get_permission_object()` which return `self.get_object()`
            or `self.object` by default.
            Default is `None`.
        any_perm (bool): Whether any of the permissions in sequence is accepted.
            Default is `False`.

    Example:
        ```python
        from guardian.mixins import PermissionRequiredMixin
        from django.views.generic import View

        class SecureView(PermissionRequiredMixin, View):
            ...
            permission_required = 'auth.change_user'
            ...
        ```
    """

    # default class view settings
    login_url: str = settings.LOGIN_URL
    permission_required: str | list[str] | None = None
    redirect_field_name: str = REDIRECT_FIELD_NAME
    return_403: bool = False
    return_404: bool = False
    raise_exception: bool = False
    object_permission_denied_message: str = ""
    accept_global_perms: bool = False
    any_perm: bool = False

    def get_object_permission_denied_message(self) -> str:
        """Get the message to pass to the `PermissionDenied` exception.

        Override this method to override the object_permission_denied_message attribute.
        """
        return self.object_permission_denied_message

    def get_required_permissions(self, request: HttpRequest | None = None) -> list[str]:
        """Get the required permissions.

        Returns list of permissions in format *<app_label>.<codename>* that
        should be checked against *request.user* and *object*.
        By default, it returns a list from `permission_required` attribute.

        Parameters:
            request (HttpRequest): Original request.
        """
        if isinstance(self.permission_required, str):
            perms = [self.permission_required]
        elif isinstance(self.permission_required, GeneratorType):
            # This feature will be removed in v4. (#666)
            warnings.warn(
                "Using generators for 'permission_required' attribute is deprecated and will be removed in v4. "
                "Use a list or tuple instead as generators can only be consumed once, "
                "potentially leading to security issues.",
                DeprecationWarning,
                stacklevel=2,
            )
            perms = [p for p in self.permission_required]
        elif isinstance(self.permission_required, Iterable):
            perms = [p for p in self.permission_required]
        else:
            raise ImproperlyConfigured(
                "'PermissionRequiredMixin' requires "
                "'permission_required' attribute to be set to "
                "'<app_label>.<permission codename>' but is set to '%s' instead" % self.permission_required
            )
        return perms

    def get_permission_object(self):
        if hasattr(self, "permission_object"):
            return self.permission_object
        return hasattr(self, "get_object") and self.get_object() or getattr(self, "object", None)

    def check_permissions(
        self, request: HttpRequest
    ) -> HttpResponseForbidden | HttpResponseNotFound | HttpResponseRedirect | HttpResponse | None:
        """Check if the user has the required permissions.

        Checks if `request.user` has all permissions returned by the
        `get_required_permissions()` method.

        Parameters:
            request (HttpRequest): The original request.
        """
        return self._check_permissions_for_object(request, self.get_permission_object())

    def _check_permissions_for_object(
        self, request: HttpRequest, obj: Model | Any | None
    ) -> HttpResponseForbidden | HttpResponseNotFound | HttpResponseRedirect | HttpResponse | None:
        """Run the permission check against an already resolved object.

        Shared by `check_permissions()` and `acheck_permissions()`. Every
        synchronous hook is called from here, so that the asynchronous version
        only needs a single thread to run all of them.
        """
        forbidden = get_40x_or_None(
            request,
            perms=self.get_required_permissions(request),
            obj=obj,
            login_url=self.login_url,
            redirect_field_name=self.redirect_field_name,
            return_403=self.return_403,
            return_404=self.return_404,
            permission_denied_message=self.get_object_permission_denied_message(),
            accept_global_perms=self.accept_global_perms,
            any_perm=self.any_perm,
        )
        if forbidden:
            self.on_permission_check_fail(request, forbidden, obj=obj)
        if forbidden and self.raise_exception:
            raise PermissionDenied(self.get_object_permission_denied_message())
        return forbidden

    def on_permission_check_fail(
        self, request: HttpRequest, response: HttpResponse, obj: Model | Any | None = None
    ) -> None:
        """Method called upon permission check fail.

        Allow subclasses to hook into the permission check failure process.
        By default, it does nothing and should only be overridden, if needed.

        Parameters:
            request (HttpRequest): Original request
            response (HttpResponse): 403 response returned by *check_permissions* method.
            obj (Model | Any): Object that was fetched from the view (using `get_object`
                method or `object` attribute, in that order).
        """

    async def aget_permission_object(self):
        """Asynchronous version of `get_permission_object()`.

        By default it runs the synchronous version in a thread, so existing
        views keep working unchanged. Override it when the object is fetched
        through the asynchronous ORM API:

        ```python
        async def aget_permission_object(self):
            return await Post.objects.aget(slug=self.kwargs["slug"])
        ```

        An asynchronous `get_permission_object()` or `get_object()` defined on
        the view is awaited as well.
        """
        if iscoroutinefunction(self.get_permission_object):
            return await self.get_permission_object()
        obj = await sync_to_async(self.get_permission_object)()
        if isawaitable(obj):
            # The view defines an asynchronous `get_object()`, whose coroutine the
            # synchronous `get_permission_object()` returned without awaiting it and
            # without reaching its fallback. Await it and apply that fallback here.
            obj = await obj or getattr(self, "object", None)
        return obj

    async def acheck_permissions(
        self, request: HttpRequest
    ) -> HttpResponseForbidden | HttpResponseNotFound | HttpResponseRedirect | HttpResponse | None:
        """Asynchronous version of `check_permissions()`.

        Parameters:
            request (HttpRequest): The original request.
        """
        obj = await self.aget_permission_object()
        return await sync_to_async(self._check_permissions_for_object)(request, obj)

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        # `view_is_async` is missing when the mixin is used outside Django's `View`.
        if _ASYNC_VIEWS_SUPPORTED and getattr(self, "view_is_async", False):
            # The returned coroutine is awaited by Django's `View.as_view()` wrapper.
            return self.adispatch(request, *args, **kwargs)
        response = self.check_permissions(request)
        if response:
            return response
        return super().dispatch(request, *args, **kwargs)

    async def adispatch(self, request, *args, **kwargs):
        """Asynchronous version of `dispatch()`, used when the view is asynchronous.

        Requires Django >= 4.2.
        """
        response = await self.acheck_permissions(request)
        if response:
            return response
        return await super().dispatch(request, *args, **kwargs)


class GuardianUserMixin:
    @staticmethod
    def get_anonymous():
        return get_anonymous_user()

    def add_obj_perm(self, perm: str, obj: Model) -> Any:
        UserObjectPermission = get_user_obj_perms_model()
        return UserObjectPermission.objects.assign_perm(perm, self, obj)

    def del_obj_perm(self, perm: str, obj: Model) -> Any:
        UserObjectPermission = get_user_obj_perms_model()
        return UserObjectPermission.objects.remove_perm(perm, self, obj)


class GuardianGroupMixin:
    def add_obj_perm(self, perm: str, obj: Model) -> Any:
        GroupObjectPermission = get_group_obj_perms_model()
        return GroupObjectPermission.objects.assign_perm(perm, self, obj)

    def del_obj_perm(self, perm: str, obj: Model) -> Any:
        GroupObjectPermission = get_group_obj_perms_model()
        return GroupObjectPermission.objects.remove_perm(perm, self, obj)


class PermissionListMixin:
    """A view mixin that filter a queryset by user and permission.

    This mixin filter object retrieved by a queryset that the
    logged-in user has the specified permission for.

    Example:
        ```python
        from django.views.generic import ListView
        from guardian.mixins import PermissionListMixin

        class SecureView(PermissionListMixin, ListView):
            ...
            permission_required = 'articles.view_article'
            ...

        # or

        class SecureView(PermissionListMixin, ListView):
            ...
            permission_required = 'auth.change_user'
            get_objects_for_user_extra_kwargs = {'use_groups': False}
            ...
        ```

    Attributes:
        permission_required (str | list[str]): permissions to check
            in format: `"<app_label>.<permission codename>"`.
            Default is `None`
        get_objects_for_user_extra_kwargs (dict): Extra params to pass to `guardian.shortcuts.get_objects_for_user`.
            Default to `{}`,
    """

    permission_required: str | list[str] | None = None
    # rename get_objects_for_user_kwargs to when get_get_objects_for_user_kwargs is removed
    get_objects_for_user_extra_kwargs: dict = {}

    def get_required_permissions(self, request: HttpRequest | None = None) -> list[str]:
        """Get the required permissions.

        Returns list of permissions in format *<app_label>.<codename>* that
        should be checked against *request.user* and *object*.
        By default, it returns a list from `permission_required` attribute.

        Parameters:
            request (HttpRequest): Original request.

        Returns:
            List of the required permissions.
        """
        if isinstance(self.permission_required, str):
            perms = [self.permission_required]
        elif isinstance(self.permission_required, GeneratorType):
            # This feature will be removed in v4. (#666)
            warnings.warn(
                "Using generators for 'permission_required' attribute is deprecated and will be removed in v4. "
                "Use a list or tuple instead as generators can only be consumed once, "
                "potentially leading to security issues.",
                DeprecationWarning,
                stacklevel=2,
            )
            perms = [p for p in self.permission_required]
        elif isinstance(self.permission_required, Iterable):
            perms = [p for p in self.permission_required]
        else:
            raise ImproperlyConfigured(
                "'PermissionRequiredMixin' requires "
                "'permission_required' attribute to be set to "
                "'<app_label>.<permission codename>' but is set to '%s' instead" % self.permission_required
            )
        return perms

    @deprecated(
        "This method is deprecated and will be removed in future versions. Use get_user_object_kwargs instead which has identical behavior."
    )
    def get_get_objects_for_user_kwargs(self, queryset: QuerySet) -> dict:
        """Get kwargs to pass to `get_objects_for_user`.

        Returns:
            dict of kwargs to be passed to `get_objects_for_user`.

        Parameters:
            queryset (QuerySet): Queryset to filter.

        Warning: Deprecation Warning
            This method is deprecated and will be removed in future versions.
            Use `get_user_object_kwargs` instead which has identical behavior.
        """
        return self.get_user_object_kwargs(queryset)

    def get_user_object_kwargs(self, queryset: QuerySet) -> dict:
        """Get kwargs to pass to `get_objects_for_user`.

        Returns:
            dict of kwargs to be passed to `get_objects_for_user`.

        Parameters:
            queryset (QuerySet): Queryset to filter.
        """
        return dict(
            user=self.request.user,  # type: ignore[attr-defined]
            perms=self.get_required_permissions(self.request),  # type: ignore[attr-defined]
            klass=queryset,
            **self.get_objects_for_user_extra_kwargs,
        )

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return get_objects_for_user(**self.get_user_object_kwargs(qs))
