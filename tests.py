"""
Unit tests runner for ``django-guardian`` based on boundled example project.
Tests are independent from this example application but setuptools need
instructions how to interpret ``test`` command when we run::

    python setup.py test

"""
import os
import sys
import django

os.environ["DJANGO_SETTINGS_MODULE"] = 'guardian.testapp.testsettings'
from guardian.testapp import testsettings as settings


def run_tests(settings):
    from django.test.utils import get_runner
    from utils import show_settings

    show_settings(settings, 'tests')

    django.setup()

    TestRunner = get_runner(settings)
    test_runner = TestRunner(interactive=False)
    failures = test_runner.run_tests(['guardian'])
    return failures

def main():
    failures = run_tests(settings)
    sys.exit(failures)

if __name__ == '__main__':
    main()
