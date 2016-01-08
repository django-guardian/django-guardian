import os
import random
import string
import environ

env = environ.Env()

DEBUG = False

ANONYMOUS_USER_ID = -1

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

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

ROOT_URLCONF = 'guardian.testapp.tests.urls'
SITE_ID = 1

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'tests', 'templates'),
)

SECRET_KEY = ''.join([random.choice(string.ascii_letters) for x in range(40)])

# Database specific

DATABASES = {'default': env.db(default="sqlite:///")}
