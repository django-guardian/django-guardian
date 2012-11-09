import django
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.auth.models import AnonymousUser


__all__ = ['User', 'Group', 'Permission', 'AnonymousUser']

# Django 1.5+ compatibility
if django.VERSION >= (1, 5):
    from django.contrib.auth import get_user_model
    User = get_user_model()
else:
    from django.contrib.auth.models import User

