from django.apps import AppConfig
from django.conf import settings

from . import monkey_patch_user, monkey_patch_group


class GuardianConfig(AppConfig):
    name = 'guardian'
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        if settings.GUARDIAN_MONKEY_PATCH_GROUP:
            monkey_patch_group()
        if settings.GUARDIAN_MONKEY_PATCH_USER:
            monkey_patch_user()
