#!/bin/sh
DB_NAME=".hidden.db"
DB_BAK_NAME=".hidden.db.bak"

if [ -f $DB_BAK_NAME ]; then
    mv $DB_BAK_NAME $DB_NAME
fi

