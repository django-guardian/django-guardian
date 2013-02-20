#!/bin/bash

echo "Running test suite with coverage report at the end"
echo -e "( would require coverage python package to be installed )\n"

OMIT="guardian/testsettings.py,guardian/compat.py"
coverage run setup.py test
coverage report --omit "$OMIT" -m guardian/*.py

