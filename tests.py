"""
Unit tests runner for ``django-guardian`` based on boundled example project.
Tests are independent from this example application but setuptools need
instructions how to interpret ``test`` command when we run::

    python setup.py test

"""
import os
import sys
import contextlib
import tempfile
import shutil


@contextlib.contextmanager
def tempdir():
    dirpath = tempfile.mkdtemp()
    prevdir = os.getcwd()

    try:
        os.chdir(dirpath)
        yield dirpath
    finally:
        os.chdir(prevdir)
        shutil.rmtree(dirpath)


def main():
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "guardian.testapp.testsettings")

    import django
    from django.core.management import call_command

    django.setup()
    with tempdir():
        call_command('test')

    sys.exit(0)

if __name__ == '__main__':
    main()
