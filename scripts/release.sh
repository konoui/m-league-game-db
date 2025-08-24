#!/bin/bash

DB_FILE=database.sqlite3
DATE=$(date +%Y%m%d)
gh release create $DATE ./$DB_FILE --title "$DATE" --notes "$DATE"
