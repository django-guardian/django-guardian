from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.auth.models import AnonymousUser
from django.utils.importlib import import_module
import six
import sys

try:
    from django.conf.urls import url, patterns, include, handler404, handler500
except ImportError:
    from django.conf.urls.defaults import url, patterns, include, handler404, handler500 # pyflakes:ignore

__all__ = [
    'User',
    'Group',
    'Permission',
    'AnonymousUser',
    'get_model_name',
    'get_user_model',
    'import_string',
    'user_model_label',
    'url',
    'patterns',
    'include',
    'handler404',
    'handler500',
    'mock',
    'unittest',
]

try:
    import unittest2 as unittest
except ImportError:
    import unittest  # pyflakes:ignore
try:
    from unittest import mock  # Since Python 3.3 mock is is in stdlib
except ImportError:
    try:
        import mock # pyflakes:ignore
    except ImportError:
        # mock is used for tests only however it is hard to check if user is
        # running tests or production code so we fail silently here; mock is
        # still required for tests at setup.py (See PR #193)
        pass

# Django 1.5 compatibility utilities, providing support for custom User models.
# Since get_user_model() causes a circular import if called when app models are
# being loaded, the user_model_label should be used when possible, with calls
# to get_user_model deferred to execution time

user_model_label = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

try:
    from django.contrib.auth import get_user_model
except ImportError:
    from django.contrib.auth.models import User
    get_user_model = lambda: User

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
    return '%s.%s_%s' % (User._meta.app_label, perm, get_model_name(User))

def get_user_permission_codename(perm):
    """
    Returns '<perm>_<usermodulename>'. If standard ``auth.User`` is
    used, for 'change' perm this would return ``change_user`` and if
    ``myapp.CustomUser`` is used it would return ``change_customuser``.
    """
    return get_user_permission_full_codename(perm).split('.')[1]


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.

    Backported from Django 1.7
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        msg = "%s doesn't look like a module path" % dotted_path
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" attribute/class' % (
            dotted_path, class_name)
        six.reraise(ImportError, ImportError(msg), sys.exc_info()[2])


# Python 3
try:
    unicode = unicode # pyflakes:ignore
    basestring = basestring # pyflakes:ignore
    str = str # pyflakes:ignore
except NameError:
    basestring = unicode = str = str

# Django 1.7 compatibility
# create_permission API changed: skip the create_models (second
# positional argument) if we have django 1.7+ and 2+ positional
# arguments with the second one being a list/tuple 
def create_permissions(*args, **kwargs):
    from django.contrib.auth.management import create_permissions as original_create_permissions
    import django

    if django.get_version().split('.')[:2] >= ['1','7'] and \
        len(args) > 1 and isinstance(args[1], (list, tuple)):
        args = args[:1] + args[2:]
    return original_create_permissions(*args, **kwargs)

__all__ = ['User', 'Group', 'Permission', 'AnonymousUser']


def get_model_name(model):
    """
    Returns model._meta.model_name on Django >=1.6 or model._meta.module_name
    on earlier versions.
    """
    if hasattr(model._meta, 'model_name'):
        return model._meta.model_name
    else:
        return model._meta.module_name
