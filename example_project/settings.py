import os
import sys

from django.conf import global_settings

abspath = lambda *p: os.path.abspath(os.path.join(*p))

DEBUG = True

PROJECT_ROOT = abspath(os.path.dirname(__file__))
GUARDIAN_MODULE_PATH = abspath(PROJECT_ROOT, '..')
sys.path.insert(0, GUARDIAN_MODULE_PATH)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': abspath(PROJECT_ROOT, '.hidden.db'),
        'TEST_NAME': ':memory:',
    },
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.messages',
    'django.contrib.flatpages',

    'native_tags',
    'guardian',
    'guardian.tests.app',
    'richtemplates',
    'django_extensions',
    'registration',
    'south',
    'django_coverage',

    'posts',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'djalog.middleware.SQLLoggingMiddleware',
)

MEDIA_ROOT = abspath(PROJECT_ROOT, 'media')
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/admin-media/'

ROOT_URLCONF = 'example_project.urls'

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    'django.core.context_processors.request',
    'richtemplates.context_processors.media',
    'example_project.context_processors.flats',
)
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
    'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates'),
)

SITE_ID = 1

USE_I18N = True
USE_L10N = True

LOGIN_REDIRECT_URL = '/'

TEST_RUNNER = 'django.test.simple.DjangoTestSuiteRunner'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

# =============== #
# DJALOG SETTINGS #
# =============== #

DJALOG_SQL = True
DJALOG_SQL_SUMMARY_ONLY = True
DJALOG_LEVEL = 5
DJALOG_USE_COLORS = True
DJALOG_FORMAT = "[%(levelname)s] %(message)s"

# ====================== #
# RICHTEMPLATES SETTINGS #
# ====================== #

RICHTEMPLATES_DEFAULT_SKIN = 'ruby'
RICHTEMPLATES_PYGMENTS_STYLES = {
    'irblack': 'richtemplates.pygstyles.irblack.IrBlackStyle',
}

ANONYMOUS_USER_ID = -1

AUTH_PROFILE_MODULE = 'richtemplates.UserProfile'

# Neede as some models (located at guardian/tests/models.py)
# are not migrated for tests
SOUTH_TESTS_MIGRATE = False

#DEBUG = False
