from __future__ import unicode_literals
import django
if django.VERSION < (1, 7):
    from django.conf import settings

    from .test_conf import *
    from .test_core import *
    from .test_custompkmodel import *
    from .test_decorators import *
    from .test_direct_rel import *
    from .test_forms import *
    from .test_managers import *
    from .test_management import *
    from .test_orphans import *
    from .test_other import *
    from .test_utils import *
    from .test_shortcuts import *
    from .test_tags import *


    if 'django.contrib.admin' in settings.INSTALLED_APPS:
        from .test_admin import *
    from .test_mixins import *

