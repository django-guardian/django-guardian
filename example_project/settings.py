import django
import os
import sys

from django.conf import global_settings

abspath = lambda *p: os.path.abspath(os.path.join(*p))

DEBUG = True
TEMPLATE_DEBUG = DEBUG
SECRET_KEY = 'CHANGE_THIS_TO_SOMETHING_UNIQUE_AND_SECURE'

TEST_SOUTH = 'GUARDIAN_TEST_SOUTH' in os.environ

PROJECT_ROOT = abspath(os.path.dirname(__file__))
GUARDIAN_MODULE_PATH = abspath(PROJECT_ROOT, '..')
sys.path.insert(0, GUARDIAN_MODULE_PATH)
sys.path.insert(0, PROJECT_ROOT)


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
    'django.contrib.staticfiles',
    'guardian',
    'guardian.tests.testapp',
    'posts',
    'core',
    'integration_tests',
)
if django.VERSION < (1, 3):
    INSTALLED_APPS += ('staticfiles',)
else:
    INSTALLED_APPS += ('django.contrib.staticfiles',)

if TEST_SOUTH:
    INSTALLED_APPS += ('south',)
if 'GRAPPELLI' in os.environ:
    try:
        __import__('grappelli')
        INSTALLED_APPS = ('grappelli',) + INSTALLED_APPS
    except ImportError:
        print("django-grappelli not installed")

#MIDDLEWARE_CLASSES = (
    #'django.middleware.common.CommonMiddleware',
    #'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.messages.middleware.MessageMiddleware',
    #'django.middleware.transaction.TransactionMiddleware',
#)

STATIC_ROOT = abspath(PROJECT_ROOT, '..', 'public', 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = [abspath(PROJECT_ROOT, 'static')]
MEDIA_ROOT = abspath(PROJECT_ROOT, 'media')
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = STATIC_URL + 'grappelli/'

ROOT_URLCONF = 'example_project.urls'

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    'django.core.context_processors.request',
    'example_project.context_processors.version',
    'django.core.context_processors.static',
)
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
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

ANONYMOUS_USER_ID = -1

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
)

# Neede as some models (located at guardian/tests/models.py)
# are not migrated for tests
SOUTH_TESTS_MIGRATE = TEST_SOUTH

AUTH_USER_MODEL = 'core.CustomUser'

try:
    from conf.localsettings import *
except ImportError:
    pass

