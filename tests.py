"""
Unit tests runner for ``django-guardian`` based on boundled example project.
Tests are independent from this example application but setuptools need
instructions how to interpret ``test`` command when we run::

    python setup.py test

"""
import os
import sys

os.environ["DJANGO_SETTINGS_MODULE"] = 'example_project.settings'
from example_project import settings

settings.DJALOG_LEVEL = 40
settings.INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.sites',
    'guardian',
)

def main():
    from django.test.utils import get_runner
    test_runner = get_runner(settings)(interactive=False)

    failures = test_runner.run_tests(['guardian'])
    sys.exit(failures)

if __name__ == '__main__':
    main()

