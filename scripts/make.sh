#!/bin/bash

(
    converter=./../m-league-score-sheet/m-converter
    cp "$converter/data/database.db" ./database.sqlite3
    # TABLE.sqlite3.md / TABLE.duckdb.md / DB_CHANGELOG.md / DB_NAMING.md / YAKU_NAMES.md / PAI_FORMAT.md は
    # m-league-score-sheet の sync-db-docs ワークフローが main へ push するので、ここでは作らない
    # クエリ作成時に参照する M リーグの情報（公開しない）
    cp ./../konoui.dev/m-ai-cat/agent/MLEAGUE.md ./MLEAGUE.md
    uv run ./scripts/render.py
)
