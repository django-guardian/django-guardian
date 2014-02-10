
from django.apps import AppConfig
from . import monkey_patch_user

class GuardianConfig(AppConfig):
    name = 'guardian'

    def ready(self):
        monkey_patch_user()
        
