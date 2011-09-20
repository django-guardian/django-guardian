#!/bin/bash

echo "Running test suite with coverage report at the end"
echo -e "( would require coverage python package to be installed )\n"

coverage run setup.py test
coverage report --omit guardian/testsettings.py -m guardian/*.py

