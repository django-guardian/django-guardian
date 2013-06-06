"""
Unit tests runner for ``django-guardian`` based on boundled example project.
Tests are independent from this example application but setuptools need
instructions how to interpret ``test`` command when we run::

    python setup.py test

"""
import os
import sys

os.environ["DJANGO_SETTINGS_MODULE"] = 'guardian.testsettings'
from guardian import testsettings as settings

settings.INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.sites',
    'guardian',
    'guardian.tests.testapp',
)
settings.PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
)

def run_tests(settings):
    from django.test.utils import get_runner
    from utils import show_settings

    show_settings(settings, 'tests')

    TestRunner = get_runner(settings)
    test_runner = TestRunner(interactive=False)
    failures = test_runner.run_tests(['auth', 'guardian'])
    return failures

def main():
    failures = run_tests(settings)
    sys.exit(failures)

if __name__ == '__main__':
    main()

