import os
import random
import string
import django

DEBUG = False

ANONYMOUS_USER_ID = -1

if django.VERSION >= (1, 5):
    AUTH_USER_MODEL = "testapp.CustomUser"
    GUARDIAN_MONKEY_PATCH = False

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.messages',
    'guardian',
    'guardian.testapp',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

# this fixes warnings in django 1.7
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

if django.VERSION < (1, 8):
    TEST_RUNNER = 'django.test.simple.DjangoTestSuiteRunner'
else:
    TEST_RUNNER = 'django.test.runner.DiscoverRunner'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST_NAME': ':memory:',
    },
}

ROOT_URLCONF = 'guardian.testapp.tests.urls'
SITE_ID = 1

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'tests', 'templates'),
)

SECRET_KEY = ''.join([random.choice(string.ascii_letters) for x in range(40)])

# Database specific

if os.environ.get('GUARDIAN_TEST_DB_BACKEND') == 'mysql':
    DATABASES['default']['ENGINE'] = 'django.db.backends.mysql'
    DATABASES['default']['NAME'] = 'guardian_test'
    DATABASES['default']['TEST_NAME'] = 'guardian_test'
    DATABASES['default']['USER'] = os.environ.get('USER', 'root')

if os.environ.get('GUARDIAN_TEST_DB_BACKEND') == 'postgresql':
    DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
    DATABASES['default']['NAME'] = 'guardian'
    DATABASES['default']['TEST_NAME'] = 'guardian_test'
    DATABASES['default']['USER'] = os.environ.get('USER', 'postgres')

