#!/bin/bash

(
    converter=./../m-league-score-sheet/m-converter
    cp "$converter/data/database.db" ./database.sqlite3
    # DuckDB 版。クエリが両方で通るかを validate-duckdb.py で検証するのに使う
    cp "$converter/data/database.duckdb" ./database.duckdb
    uv run ./scripts/render.py
)
