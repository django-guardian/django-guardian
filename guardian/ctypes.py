from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType

from guardian.conf import settings as guardian_settings
from guardian.compat import import_string


def get_content_type(obj):
    get_content_type_function = import_string(
        guardian_settings.GET_CONTENT_TYPE)
    return get_content_type_function(obj)


def get_default_content_type(obj):
    return ContentType.objects.get_for_model(obj)


#
# Just for example. Will not be included with django-guardian.
#
def get_polymorphic_base_content_type(obj):
    """
    Special helper function to return BASE polymorphic ctype id
    """
    if hasattr(obj, 'polymorphic_model_marker'):
        try:
            superclasses = list(obj.__class__.mro())
        except TypeError:
            # obj is an object so mro() need to be called with the obj.
            superclasses = list(obj.__class__.mro(obj))

        polymorphic_superclasses = list()
        for sclass in superclasses:
            if hasattr(sclass, 'polymorphic_model_marker'):
                polymorphic_superclasses.append(sclass)

        # PolymorphicMPTT adds an additional class between polymorphic and
        # base class
        if hasattr(obj, 'can_have_children'):
            root_polymorphic_class = polymorphic_superclasses[-3]
        else:
            root_polymorphic_class = polymorphic_superclasses[-2]
        ctype = ContentType.objects.get_for_model(root_polymorphic_class)

    else:
        ctype = ContentType.objects.get_for_model(obj)

    return ctype
