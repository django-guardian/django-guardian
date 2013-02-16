#!/bin/sh
DB_NAME=".hidden.db"
DB_BAK_NAME=".hidden.db.bak"

if [ -f $DB_BAK_NAME ]; then
    mv $DB_NAME $DB_BAK_NAME
fi

