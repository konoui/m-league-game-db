#!/bin/bash

(
    converter=./../m-league-score-sheet/m-converter
    cp "$converter/data/database.db" ./database.sqlite3
    uv run --quiet --with pyyaml python ./scripts/make-table-doc.py "$converter/table-doc.yaml" ./TABLE.md
    cp "$converter/YAKU_NAMES.md" ./YAKU_NAMES.md
    cp "$converter/PAI_FORMAT.md" ./PAI_FORMAT.md
    rm -f ./query-examples/*
    cp ./../m-league-sql-summarizer/markdown/* ./query-examples/
    cp ./../m-league-sql-summarizer/scripts/query-helper.sh  ./scripts/query-helper.sh
    ./scripts/make-query-readme.sh
)
