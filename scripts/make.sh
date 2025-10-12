#!/bin/bash

(
    cp ./../m-league-score-sheet/m-converter/data/database.db ./database.sqlite3
    cp ./../m-league-score-sheet/m-converter/TABLE.md ./TABLE.md
    rm -f ./query-examples/*
    cp ./../m-league-sql-summarizer/markdown/* ./query-examples/
    ./scripts/make-query-readme.sh
)
