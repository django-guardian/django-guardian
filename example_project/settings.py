import os
import sys
from django.conf import global_settings
import environ

env = environ.Env()

abspath = lambda *p: os.path.abspath(os.path.join(*p))


DEBUG = True
TEMPLATE_DEBUG = DEBUG
SECRET_KEY = 'CHANGE_THIS_TO_SOMETHING_UNIQUE_AND_SECURE'

PROJECT_ROOT = abspath(os.path.dirname(__file__))
GUARDIAN_MODULE_PATH = abspath(PROJECT_ROOT, '..')
sys.path.insert(0, GUARDIAN_MODULE_PATH)

DATABASES = {'default': env.db(default="sqlite://./example.db")}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.messages',
    'guardian',
    'posts',
    'articles',
    'core',
    'django.contrib.staticfiles',
)

if 'GRAPPELLI' in os.environ:
    try:
        __import__('grappelli')
        INSTALLED_APPS = ('grappelli',) + INSTALLED_APPS
    except ImportError:
        print("django-grappelli not installed")

try:
    import rosetta
    INSTALLED_APPS += ('rosetta',)
except ImportError:
    pass

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

STATIC_ROOT = abspath(PROJECT_ROOT, '..', 'public', 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = [abspath(PROJECT_ROOT, 'static')]
GUARDIAN_RAISE_403 = True

ROOT_URLCONF = 'urls'

TEMPLATE_CONTEXT_PROCESSORS = (
    'context_processors.version',
    "django.contrib.auth.context_processors.auth",
    "django.template.context_processors.debug",
    "django.template.context_processors.i18n",
    "django.template.context_processors.media",
    "django.template.context_processors.static",
    "django.template.context_processors.request",
    "django.template.context_processors.tz",
    "django.contrib.messages.context_processors.messages"
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

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

GUARDIAN_GET_INIT_ANONYMOUS_USER = 'core.models.get_custom_anon_user'

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
)

AUTH_USER_MODEL = 'core.CustomUser'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': TEMPLATE_DIRS,
        'OPTIONS': {
            'debug': TEMPLATE_DEBUG,
            'loaders': TEMPLATE_LOADERS,
            'context_processors': TEMPLATE_CONTEXT_PROCESSORS,
        },
    },
]
