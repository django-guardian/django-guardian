
from django.apps import AppConfig
from . import monkey_patch_user
from guardian.conf.settings import MONKEY_PATCH


class GuardianConfig(AppConfig):
    name = 'guardian'

    def ready(self):
        if MONKEY_PATCH:
            monkey_patch_user()
        
