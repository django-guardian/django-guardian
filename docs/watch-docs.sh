#!/bin/sh

DIR="."
CMD="make html"
NOTIFY='growlnotify guardian Documentation -m Recreated'


# Run command
echo " => Documentation would be available at file://$PWD/build/html/index.html"
$CMD
$NOTIFY

# Run command on .rst file change.
watchmedo shell-command --pattern "*.rst" --recursive -w -c "clear && $CMD && $NOTIFY" $DIR

