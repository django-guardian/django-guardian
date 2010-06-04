#!/bin/bash

echo "Running test suite with coverage report at the end"
echo -e "( would require coverage python package to be installed )\n"

coverage run setup.py test
coverage report -m --omit=example_project,setup,tests,guardian/tests,guardian/conf/settings

