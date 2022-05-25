from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from django.utils.module_loading import import_string

from guardian.conf import settings as guardian_settings


def get_content_type(obj):
    get_content_type_function = import_string(
        guardian_settings.GET_CONTENT_TYPE)
    return get_content_type_function(obj)


def get_content_type_from_iterable_or_object(iterable_or_object):
    if isinstance(iterable_or_object, list):
        ctype = get_content_type(iterable_or_object[0])
    elif isinstance(iterable_or_object, QuerySet):
        ctype = get_content_type(iterable_or_object.model)
    else:
        ctype = get_content_type(iterable_or_object)

    return ctype


def get_default_content_type(obj):
    return ContentType.objects.get_for_model(obj)
