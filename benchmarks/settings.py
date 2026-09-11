import os
import sys

import environ

env = environ.Env()


def abspath(*args):
    """Join path arguments and return their absolute path"""
    return os.path.abspath(os.path.join(*args))


THIS_DIR = abspath(os.path.dirname(__file__))
ROOT_DIR = abspath(THIS_DIR, "..")

# so the preferred guardian module is one within this repo and
# not system-wide
sys.path.insert(0, ROOT_DIR)

SECRET_KEY = "NO_NEED_SECRET"

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    "django.contrib.admin",
    "django.contrib.sites",
    "guardian",
    "benchmarks",
)

DJALOG_LEVEL = 40

DATABASES = {"default": env.db(default="sqlite:///")}
