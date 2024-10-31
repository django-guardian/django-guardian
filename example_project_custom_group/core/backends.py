from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Permission


class CustomModelBackend(ModelBackend):
    """ Overriding the default ModelBackend to fix the group permissions issue:
    https://code.djangoproject.com/ticket/35792."""

    def _get_group_permissions(self, user_obj):
        return Permission.objects.filter(group__in=user_obj.groups.all())
