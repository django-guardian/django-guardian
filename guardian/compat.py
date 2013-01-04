import django
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.auth.models import AnonymousUser

try:
    from django.conf.urls import url, patterns, include, handler404, handler500
except ImportError:
    from django.conf.urls.defaults import url, patterns, include, handler404, handler500

__all__ = [
    'User',
    'Group',
    'Permission',
    'AnonymousUser',
    'url',
    'patterns',
    'include',
    'handler404',
    'handler500'
]

# Django 1.5+ compatibility
if django.VERSION >= (1, 5):
    from django.contrib.auth import get_user_model
    User = get_user_model()
else:
    from django.contrib.auth.models import User

