#!/bin/bash
set -eux

# Lint modern PY3 syntax
find . -name '*.py' | xargs pyupgrade --py3-only

# Code tests
python ./setup.py --version
py.test --cov=guardian

# Test example_project on supported django versions
if [ "${DJANGO_VERSION:0:3}" = "2.1" ] || \
   [ "${DJANGO_VERSION:0:3}" = "2.2" ] || \
   [ "$DJANGO_VERSION" = "master" ]; then
    pip install .;
    cd example_project;
    python -Wa manage.py makemigrations --check --dry-run;
    python -We manage.py test;
fi;
