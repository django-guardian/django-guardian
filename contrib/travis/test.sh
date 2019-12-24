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
python -Wa manage.py makemigrations --check --dry-run;
python -Wa manage.py test;
