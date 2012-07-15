import django
from django.conf import settings

from conf_test import *
from core_test import *
from custompkmodel_test import *
from decorators_test import *
from forms_test import *
from orphans_test import *
from other_test import *
from utils_test import *
from shortcuts_test import *
from tags_test import *


if 'django.contrib.admin' in settings.INSTALLED_APPS:
    from admin_test import *

if django.VERSION >= (1, 3):
    from mixins_test import *

