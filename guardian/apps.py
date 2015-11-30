
from django.apps import AppConfig
from . import monkey_patch_user
from guardian.conf import settings


class GuardianConfig(AppConfig):
    name = 'guardian'

    def ready(self):
        if settings.MONKEY_PATCH:
            monkey_patch_user()
