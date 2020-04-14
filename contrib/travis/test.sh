#!/bin/bash
set -eux

# Lint modern PY3 syntax
find . -name '*.py' | xargs pyupgrade --py3-only

# Code tests
python ./setup.py --version
py.test --cov=guardian

# Test example_project
pip install .;
cd example_project;
EXAMPLE_PROJECTS_DJANGO_VERSION=$(grep -i "django[^-]" requirements.txt | cut -d "=" -f 2)
if [ "${DJANGO_VERSION:0:3}" = "${EXAMPLE_PROJECTS_DJANGO_VERSION:0:3}" ]; then
    python -Wa manage.py makemigrations --check --dry-run;
elif [ -z "${EXAMPLE_PROJECTS_DJANGO_VERSION}" ]; then
    echo "Could not determine which version of Django the example project supports."
    exit 1
fi;
python -Wa manage.py test;
