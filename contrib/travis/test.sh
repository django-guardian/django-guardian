#!/bin/sh

python ./setup.py --version
py.test --cov=guardian

# Tests django example on supported;
if [[ $DJANGO_VERSION = 1.10 || $DJANGO_VERSION = 1.11 || $DJANGO_VERSION = 2.0 || $DJANGO_VERSION = "master" ]]; then
    pip install .; 
    cd example_project; 
    python manage.py test;
fi;
