#!/bin/bash

DB_FILE=database.sqlite3
ZIP_DB_FILE=database.zip
DATE=$(date +%Y%m%d)
zip -j ./$ZIP_DB_FILE ./$DB_FILE
gh release create $DATE ./$ZIP_DB_FILE --generate-notes
