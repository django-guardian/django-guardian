"""
Unit tests runner for ``django-guardian`` based on boundled example project.
Tests are independent from this example application but setuptools need
instructions how to interpret ``test`` command when we run::

    python setup.py test

"""
import os
import sys
import django

os.environ["DJANGO_SETTINGS_MODULE"] = 'guardian.testsettings'
from guardian import testsettings as settings

settings.INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.sites',
    'guardian',
    'guardian.testapp',
)
settings.PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
)

def run_tests(settings):
    from django.test.utils import get_runner
    from utils import show_settings

    show_settings(settings, 'tests')

    import django
    if hasattr(django, 'setup'):
        django.setup()

    TestRunner = get_runner(settings)
    test_runner = TestRunner(interactive=False)
    # As we use different TestRunners for django < 1.8 and >= 1.8
    # the arguments run_tests differs
    if django.VERSION < (1, 8):
        failures = test_runner.run_tests(['auth', 'guardian', 'testapp'])
    else:
        failures = test_runner.run_tests([
            'django.contrib.auth', 'guardian', 'guardian.testapp'])
    return failures

def main():
    failures = run_tests(settings)
    sys.exit(failures)

if __name__ == '__main__':
    main()
