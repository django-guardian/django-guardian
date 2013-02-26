#!/usr/bin/env python
import django
import sys
from django.core.management import execute_manager
try:
    import settings # Assumed to be in the same directory.
except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

def main():
    if django.VERSION < (1, 3):
        sys.stderr.write("guardian's example project requires Django 1.3+\n")
        sys.exit(1)
    execute_manager(settings)

if __name__ == "__main__":
    main()

