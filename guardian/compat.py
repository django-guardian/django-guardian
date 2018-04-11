from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import handler404, handler500, include, url
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group, Permission
from importlib import import_module

import django
import six
import sys

__all__ = [
    'User',
    'Group',
    'Permission',
    'AnonymousUser',
    'get_user_model',
    'user_model_label',
    'url',
    'patterns',
    'include',
    'handler404',
    'handler500',
]

# Since get_user_model() causes a circular import if called when app models are
# being loaded, the user_model_label should be used when possible, with calls
# to get_user_model deferred to execution time

user_model_label = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


def get_user_model_path():
    """
    Returns 'app_label.ModelName' for User model. Basically if
    ``AUTH_USER_MODEL`` is set at settings it would be returned, otherwise
    ``auth.User`` is returned.
    """
    return getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


def get_user_permission_full_codename(perm):
    """
    Returns 'app_label.<perm>_<usermodulename>'. If standard ``auth.User`` is
    used, for 'change' perm this would return ``auth.change_user`` and if
    ``myapp.CustomUser`` is used it would return ``myapp.change_customuser``.
    """
    User = get_user_model()
    model_name = User._meta.model_name
    return '%s.%s_%s' % (User._meta.app_label, perm, model_name)


def get_user_permission_codename(perm):
    """
    Returns '<perm>_<usermodulename>'. If standard ``auth.User`` is
    used, for 'change' perm this would return ``change_user`` and if
    ``myapp.CustomUser`` is used it would return ``change_customuser``.
    """
    return get_user_permission_full_codename(perm).split('.')[1]


# Python 3
try:
    unicode = unicode  # pyflakes:ignore
    basestring = basestring  # pyflakes:ignore
    str = str  # pyflakes:ignore
except NameError:
    basestring = unicode = str = str


# Django 1.7 compatibility
# create_permission API changed: skip the create_models (second
# positional argument) if we have django 1.7+ and 2+ positional
# arguments with the second one being a list/tuple
def create_permissions(*args, **kwargs):
    from django.contrib.auth.management import create_permissions as original_create_permissions

    if len(args) > 1 and isinstance(args[1], (list, tuple)):
        args = args[:1] + args[2:]
    return original_create_permissions(*args, **kwargs)

__all__ = ['User', 'Group', 'Permission', 'AnonymousUser']
