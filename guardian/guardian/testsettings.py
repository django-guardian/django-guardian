import os

DEBUG = False

ANONYMOUS_USER_ID = -1

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.messages',
    'guardian',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

TEST_RUNNER = 'django.test.simple.DjangoTestSuiteRunner'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST_NAME': ':memory:',
    },
}

ROOT_URLCONF = 'guardian.tests.urls'
SITE_ID = 1

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'tests', 'templates'),
)
print TEMPLATE_DIRS

