#!/usr/bin/env python
import django
import os
import sys

if django.VERSION < (1, 5):
    sys.stderr.write("ERROR: guardian's example project must be run with "
                     "Django 1.5 or later!\n")
    sys.exit(1)


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
