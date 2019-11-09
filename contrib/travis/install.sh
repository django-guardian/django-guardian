#!/bin/bash

set -ev

pip install -U pip

# Array of packages
PACKAGES=('mock==1.0.1' 'pytest' 'pytest-django' 'pytest-cov' 'django-environ' 'setuptools_scm' 'pyupgrade')

# Install django master or version
if [[ "$DJANGO_VERSION" == 'master' ]]; then
    PACKAGES+=('https://github.com/django/django/archive/master.tar.gz');
else
    PACKAGES+=("Django==$DJANGO_VERSION");
fi;

# Install database drivers
if [[ $DATABASE_URL = postgres* ]]; then
    PACKAGES+=('psycopg2-binary==2.8.4');
    psql -c 'create database django_guardian;' -U postgres;
    psql -c 'create database test_django_guardian;' -U postgres;
fi;

if [[ $DATABASE_URL = mysql* ]]; then
    PACKAGES+=('mysqlclient==1.4.5');
    mysql -e 'CREATE DATABASE django_guardian;';
    mysql -e 'CREATE DATABASE test_django_guardian;';
fi;
echo "Install " ${PACKAGES[*]};
pip install --upgrade --upgrade-strategy=only-if-needed ${PACKAGES[*]};
pip check
