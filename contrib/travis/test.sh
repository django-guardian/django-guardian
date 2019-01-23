#!/bin/bash

python ./setup.py --version
py.test --cov=guardian

# Test example_project on supported django versions
if [ "${DJANGO_VERSION:0:3}" = "1.11" ] || \
   [ "${DJANGO_VERSION:0:3}" = "2.0" ] || \
   [ "${DJANGO_VERSION:0:3}" = "2.1" ] || \
   [ "${DJANGO_VERSION:0:3}" = "2.2" ] || \
   [ "$DJANGO_VERSION" = "master" ]; then
    pip install .; 
    cd example_project; 
    python -Wa manage.py test;
fi;
