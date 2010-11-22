from django.contrib import admin

from guardian.admin import GuardedModelAdmin
from guardian.tests.app.models import Keycard

class KeycardGuardedAdmin(GuardedModelAdmin):
    pass

admin.site.register(Keycard, KeycardGuardedAdmin)

