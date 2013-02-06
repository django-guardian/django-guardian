import logging
from .shortcuts import get_perms_for_model, assign

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.functional import wraps
from django.db.models import Model, get_model
from django.db.models.base import ModelBase
from django.db.models.query import QuerySet
from django.db.models.signals import post_save
from django.shortcuts import get_object_or_404
from guardian.exceptions import GuardianError
from guardian.utils import get_403_or_None
from guardian.conf import settings as guardian_settings
from django.contrib.auth.models import User


def permission_required(perm, lookup_variables=None, **kwargs):
    """
    Decorator for views that checks whether a user has a particular permission
    enabled.

    Optionally, instances for which check should be made may be passed as an
    second argument or as a tuple parameters same as those passed to
    ``get_object_or_404`` but must be provided as pairs of strings.

    :param login_url: if denied, user would be redirected to location set by
      this parameter. Defaults to ``django.conf.settings.LOGIN_URL``.
    :param redirect_field_name: name of the parameter passed if redirected.
      Defaults to ``django.contrib.auth.REDIRECT_FIELD_NAME``.
    :param return_403: if set to ``True`` then instead of redirecting to the
      login page, response with status code 403 is returned (
      ``django.http.HttpResponseForbidden`` instance or rendered template -
      see :setting:`GUARDIAN_RENDER_403`). Defaults to ``False``.
    :param accept_global_perms: if set to ``True``, then *object level
      permission* would be required **only if user does NOT have global
      permission** for target *model*. If turned on, makes this decorator
      like an extension over standard
      ``django.contrib.admin.decorators.permission_required`` as it would
      check for global permissions first. Defaults to ``False``.

    Examples::

        @permission_required('auth.change_user', return_403=True)
        def my_view(request):
            return HttpResponse('Hello')

        @permission_required('auth.change_user', (User, 'username', 'username'))
        def my_view(request, username):
            user = get_object_or_404(User, username=username)
            return user.get_absolute_url()

        @permission_required('auth.change_user',
            (User, 'username', 'username', 'groups__name', 'group_name'))
        def my_view(request, username, group_name):
            user = get_object_or_404(User, username=username,
                group__name=group_name)
            return user.get_absolute_url()

    """
    login_url = kwargs.pop('login_url', settings.LOGIN_URL)
    redirect_field_name = kwargs.pop('redirect_field_name', REDIRECT_FIELD_NAME)
    return_403 = kwargs.pop('return_403', False)
    accept_global_perms = kwargs.pop('accept_global_perms', False)

    # Check if perm is given as string in order not to decorate
    # view function itself which makes debugging harder
    if not isinstance(perm, basestring):
        raise GuardianError("First argument must be in format: "
            "'app_label.codename or a callable which return similar string'")

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            # if more than one parameter is passed to the decorator we try to
            # fetch object for which check would be made
            obj = None
            if lookup_variables:
                model, lookups = lookup_variables[0], lookup_variables[1:]
                # Parse model
                if isinstance(model, basestring):
                    splitted = model.split('.')
                    if len(splitted) != 2:
                        raise GuardianError("If model should be looked up from "
                            "string it needs format: 'app_label.ModelClass'")
                    model = get_model(*splitted)
                elif issubclass(model.__class__, (Model, ModelBase, QuerySet)):
                    pass
                else:
                    raise GuardianError("First lookup argument must always be "
                        "a model, string pointing at app/model or queryset. "
                        "Given: %s (type: %s)" % (model, type(model)))
                # Parse lookups
                if len(lookups) % 2 != 0:
                    raise GuardianError("Lookup variables must be provided "
                        "as pairs of lookup_string and view_arg")
                lookup_dict = {}
                for lookup, view_arg in zip(lookups[::2], lookups[1::2]):
                    if view_arg not in kwargs:
                        raise GuardianError("Argument %s was not passed "
                            "into view function" % view_arg)
                    lookup_dict[lookup] = kwargs[view_arg]
                obj = get_object_or_404(model, **lookup_dict)

            response = get_403_or_None(request, perms=[perm], obj=obj,
                login_url=login_url, redirect_field_name=redirect_field_name,
                return_403=return_403, accept_global_perms=accept_global_perms)
            if response:
                return response
            return view_func(request, *args, **kwargs)
        return wraps(view_func)(_wrapped_view)
    return decorator


def permission_required_or_403(perm, *args, **kwargs):
    """
    Simple wrapper for permission_required decorator.

    Standard Django's permission_required decorator redirects user to login page
    in case permission check failed. This decorator may be used to return
    HttpResponseForbidden (status 403) instead of redirection.

    The only difference between ``permission_required`` decorator is that this
    one always set ``return_403`` parameter to ``True``.
    """
    kwargs['return_403'] = True
    return permission_required(perm, *args, **kwargs)


def owned_by(owner_lookup, *perms, **kwargs):
    """
    The user specified by ``owner_lookup`` will be assigned permissions in ``perms``, or all available permissions on the decorated model class.
    """
    def decorator(cls):
        ownership_chain = owner_lookup.split('__')

        def add_owner_permissions(sender, instance, created, raw, **kwargs):
            """
            Assigns all or specified permissions on ``instance`` to its owner when ``instance`` is created.
            """
            # stop if it's syncdb (raw) or if it's not a child model
            if not created or raw or not isinstance(instance, cls):
                return

            owner = instance
            for name in ownership_chain:
                owner = getattr(owner, name)

            #import ipdb; ipdb.set_trace()

            for perm in perms or (p.codename for p in get_perms_for_model(cls)):
                logging.debug('assigning %s to %s on %s' % (perm, owner, instance))
                assign(perm, owner, cls._default_manager.get(pk=instance.pk))

        extra = {'sender': cls} if not kwargs.get('include_children') else {}
        post_save.connect(add_owner_permissions, weak=False, **extra)
        logging.debug('Permissions on model %s will be installed automatically' % cls)
        return cls

    return decorator

DEFAULT_PERMISSIONS = []


def default_model_permissions(*perms):
    """
    Every new user will have ``perms`` on the decorated model.
    """
    if not perms:
        raise ValueError('Supply at least 1 permission')

    def decorator(cls):
        logging.debug('creating default permissions %s on %s' % (perms, cls))
        DEFAULT_PERMISSIONS.extend(perms)
        return cls

    return decorator


def assign_default_permissions(sender, instance, created, raw, **kwargs):
    """
    Assigns default model-wide permissions when a new User is created.
    """
    # do not do anything when user is updated or created from fixtures (raw)
    # Guardian defines AnonymousUser in its model files, so this user is created
    # before any of the site models is defined => permissions in the list
    # do not exist yet.
    if created and not raw and instance.pk != guardian_settings.ANONYMOUS_USER_ID:
        for perm in DEFAULT_PERMISSIONS:
            logging.debug('assigning model-wide permission %s to %s' % (perm, instance))
            assign(perm, instance)  # TODO: rewrite this to use bulk permission creation

post_save.connect(assign_default_permissions, sender=User, weak=False)
