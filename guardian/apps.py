from . import monkey_patch_user
from django.apps import AppConfig
from guardian.conf import settings


class GuardianConfig(AppConfig):
    name = 'guardian'

    def ready(self):
        if settings.MONKEY_PATCH:
            monkey_patch_user()
