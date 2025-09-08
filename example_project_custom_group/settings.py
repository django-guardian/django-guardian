import os
import sys

import environ

env = environ.Env()


def abspath(*args):
    """Join path arguments and return their absolute path"""
    return os.path.abspath(os.path.join(*args))


DEBUG = True
SECRET_KEY = "CHANGE_THIS_TO_SOMETHING_UNIQUE_AND_SECURE"

PROJECT_ROOT = abspath(os.path.dirname(__file__))
GUARDIAN_MODULE_PATH = abspath(PROJECT_ROOT, "..")
sys.path.insert(0, GUARDIAN_MODULE_PATH)

DATABASES = {"default": env.db(default="sqlite:///example.db")}

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.admin",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "guardian",
    "posts",
    "articles",
    "core",
)

if "GRAPPELLI" in os.environ:
    try:
        __import__("grappelli")
        INSTALLED_APPS = ("grappelli",) + INSTALLED_APPS
    except ImportError:
        print("django-grappelli not installed")

MIDDLEWARE = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
)

STATIC_ROOT = abspath(PROJECT_ROOT, "..", "public", "static")
STATIC_URL = "/static/"
STATICFILES_DIRS = [abspath(PROJECT_ROOT, "static")]
GUARDIAN_RAISE_403 = True

ROOT_URLCONF = "urls"

SITE_ID = 1

USE_I18N = True
USE_L10N = True
USE_TZ = True
TIME_ZONE = "UTC"

LOGIN_REDIRECT_URL = "/"

TEST_RUNNER = "django.test.runner.DiscoverRunner"

AUTHENTICATION_BACKENDS = (
    # This custom backend is needed as long as https://github.com/django/django/commit/d4e4520efb553d2bfcc68ac8cf007c0c402d4845
    # is not added to a Django release, after that we can just enable it for the relevant versions (>5.1.2).
    "core.backends.CustomModelBackend",
    "guardian.backends.ObjectPermissionBackend",
)

GUARDIAN_GET_INIT_ANONYMOUS_USER = "core.models.get_custom_anon_user"

PASSWORD_HASHERS = ("django.contrib.auth.hashers.PBKDF2PasswordHasher",)

AUTH_USER_MODEL = "core.CustomUser"
GUARDIAN_USER_OBJ_PERMS_MODEL = "articles.BigUserObjectPermission"
GUARDIAN_GROUP_OBJ_PERMS_MODEL = "articles.BigGroupObjectPermission"

GUARDIAN_MONKEY_PATCH_USER = False
GUARDIAN_MONKEY_PATCH_GROUP = False


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": (os.path.join(os.path.dirname(__file__), "templates"),),
        "OPTIONS": {
            "debug": DEBUG,
            "loaders": (
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ),
            "context_processors": (
                "core.context_processors.version",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.request",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ),
        },
    },
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
