#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    # should be ../../ (`djangoguardian/`)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    sys.path.append(BASE_DIR)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "guardian.testapp.testsettings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
