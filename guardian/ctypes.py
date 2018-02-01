from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType

from guardian.conf import settings as guardian_settings
from guardian.compat import import_string


def get_content_type(model):
    get_content_type_function = import_string(
        guardian_settings.GET_CONTENT_TYPE)
    return get_content_type_function(model)


def get_default_content_type(model):
    return ContentType.objects.get_for_model(model)
