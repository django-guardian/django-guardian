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

