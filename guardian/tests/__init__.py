import django
from django.conf import settings

from conf_test import * # pyflakes:ignore
from core_test import * # silence pyflakes
from custompkmodel_test import * # silence pyflakes
from decorators_test import * # silence pyflakes
from forms_test import * # silence pyflakes
from orphans_test import * # silence pyflakes
from other_test import * # silence pyflakes
from utils_test import * # silence pyflakes
from shortcuts_test import * # silence pyflakes
from tags_test import * # silence pyflakes


if 'django.contrib.admin' in settings.INSTALLED_APPS:
    from admin_test import * # silence pyflakes

if django.VERSION >= (1, 3):
    from mixins_test import * # silence pyflakes

